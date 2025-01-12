import boto3
from botocore.exceptions import UnknownServiceError
from flask import _app_ctx_stack as stack
from flask import current_app


class Boto3(object):
    """Stores a bunch of boto3 conectors inside Flask's application context
    for easier handling inside view functions.

    All connectors are stored inside the dict `boto3_cns` where the keys are
    the name of the services and the values their associated boto3 resource/client.

    Cf: https://github.com/shiyuangu/flask-boto3
    Usage example: 

    from flask import Flask
    from flask_boto3 import Boto3
    app = Flask(__name__)
    app.config['BOTO3_SERVICES'] = ['s3']
    boto_flask = Boto3(app)
    
   T hen boto3's clients and resources will be available as properties within the application context:    
    >>> with app.app_context():
        print(boto_flask.clients)
        print(boto_flask.resources)
    {'s3': <botocore.client.S3 object at 0x..>}
    {'s3': s3.ServiceResource()}
    
    """

    def __init__(self, app=None):
        self.app = app
        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.teardown_appcontext(self.teardown)

    def connect(self):
        """Iterate through the application configuration and instantiate
        the services.
        """
        requested_services = set(
            svc.lower() for svc in current_app.config.get('BOTO3_SERVICES', [])
        )

        region = current_app.config.get('BOTO3_REGION',"us-west-1") # N. California
        sess_params = {

            # BOTO3_XXX is for flask-boto3; if None, rely on default lookup 
            'aws_access_key_id': current_app.config.get('BOTO3_ACCESS_KEY'),
            'aws_secret_access_key': current_app.config.get('BOTO3_SECRET_KEY'),

            # To use the default profile, don’t set the profile_name parameter at all.
            # Cf: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/session.html#session-configurations
            # Cf: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
            'profile_name': current_app.config.get('BOTO3_PROFILE'), 
            'region_name': region
        }
        sess = boto3.session.Session(**sess_params) # pyright: ignore

        try:
            cns = {}
            for svc in requested_services:
                # Check for optional parameters
                params = current_app.config.get(
                    'BOTO3_OPTIONAL_PARAMS', {}
                ).get(svc, {})

                # Get session params and override them with kwargs
                # `profile_name` cannot be passed to clients and resources
                kwargs = sess_params.copy()
                kwargs.update(params.get('kwargs', {}))
                del kwargs['profile_name']

                # Override the region if one is defined as an argument
                args = params.get('args', [])
                if len(args) >= 1:
                    del kwargs['region_name']

                if not(isinstance(args, list) or isinstance(args, tuple)):
                    args = [args]

                # Create resource or client
                # use resource API if available otherwise use low level client api
                if svc in sess.get_available_resources():
                    cns.update({svc: sess.resource(svc, *args, **kwargs)})
                else:
                    cns.update({svc: sess.client(svc, *args, **kwargs)})
        except UnknownServiceError:
            raise
        return cns

    def teardown(self, exception): 
        ctx = stack.top
        if hasattr(ctx, 'boto3_cns'):
            for c in ctx.boto3_cns:
                con = ctx.boto3_cns[c]
                if hasattr(con, 'close') and callable(con.close):
                    ctx.boto3_cns[c].close()

    @property
    def resources(self):
        c = self.connections

        # the existence of svc.meta.client indicates the service has resouce. 
        return {k: v for k, v in c.items() if hasattr(c[k].meta, 'client')}  # pyright: ignore

    @property
    def clients(self):
        """
        Get all clients (with and without associated resources)
        """
        clients = {}
        for k, v in self.connections.items():  # pyright: ignore
            if hasattr(v.meta, 'client'):       # has boto3 resource
                clients[k] = v.meta.client
            else:                               # no boto3 resource
                clients[k] = v
        return clients

    @property
    def connections(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'boto3_cns'):
                ctx.boto3_cns = self.connect()
            return ctx.boto3_cns
