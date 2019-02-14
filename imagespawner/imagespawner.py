from marathonspawner import MarathonSpawner
from tornado import gen
from traitlets import default, Unicode, List
import datetime

class MarathonImageChooserSpawner(MarathonSpawner):
    '''Enable the user to select the docker image that gets spawned.
    
    Define the available docker images in the JupyterHub configuration and pull
    them to the execution nodes:

    c.JupyterHub.spawner_class = DockerImageChooserSpawner
    c.DockerImageChooserSpawner.dockerimages = [
        'jupyterhub/singleuser',
        'jupyter/r-singleuser'
    ]
    '''
    
    dockerimages = List(
        trait = Unicode(),
        default = ["perilousapricot/cms-jupyter"],
        minlen = 1,
        config = True,
        help = "Docker Images"
    )
    dockertitles = List(
        trait = Unicode(),
        default = ["Default ACCRE Image"],
        minlen = 1,
        config = True,
        help = "Docker Image Descriptions"
    )
    form_template = Unicode("""
        <label for="dockerimage">Select a Docker image:</label>
        <select class="form-control" name="dockerimage" required autofocus>
            {docker_option_template}
        </select>
        <label for="resources">Select a container size:</label>
        <select class="form-control" name="resources" required>
            {resource_option_template}
        </select>
        
        """,
        config = True, help = "Form template."
    )
    option_template = Unicode("""
            <option value="{image}">{title}</option>\n""",
        config = True, help = "Template for html form options."
    )

    def get_allowed_resources(self, config):
        if self.user.orm_user.name in config['resource_mapping']:
            allowed_types = config['resource_mapping'][self.user.orm_user.name]
        elif self.user.orm_user.admin:
            allowed_types = config['resources'].keys()
        else:
            allowed_types = config['resource_mapping']['default']
        return allowed_types

    @default('options_form')
    def _options_form(self):
        """Return the form with the drop-down menu."""
        import json
        config = json.loads(open('/data/spawn.json', 'r').read())
        docker_options = ''.join([
            self.option_template.format(image=di, title=dt) for (di,dt) in zip(config['dockerimages'], config['dockertitles'])
        ])
        allowed_types = self.get_allowed_resources(config)
        resource_options = "".join([self.option_template.format(image=x,title=config['resources'][x]['title']) for x in allowed_types])
        return self.form_template.format(docker_option_template=docker_options, resource_option_template=resource_options)

    def options_from_form(self, formdata):
        """Parse the submitted form data and turn it into the correct
           structures for self.user_options."""
        import json
        config = json.loads(open('/data/spawn.json', 'r').read())

        defaultimage = config['dockerimages'][0]

        # formdata looks like {'dockerimage': ['jupyterhub/singleuser']}"""
        dockerimage = formdata.get('dockerimage', [defaultimage])[0]

        # Don't allow users to input their own images
        if dockerimage not in config['dockerimages']: dockerimage = default

        defaultresource = config['resource_mapping']['default'][0]
        formresource = formdata.get('resources', [defaultresource])[0]
        self.log.info("got formresrou: %s", formresource)
        allowed_types = self.get_allowed_resources(config)
        self.log.info("User %s is allowed these node types: %s", self.user.orm_user.name, allowed_types)       

        if formresource not in allowed_types: formresource = defaultresource
        resourceconfig = config['resources'][formresource]
        # container_prefix: The prefix of the user's container name is inherited 
        # from DockerSpawner and it defaults to "jupyter". Since a single user may launch different containers
        # (even though not simultaneously), they should have different
        # prefixes. Otherwise docker will only save one container per user. We
        # borrow the image name for the prefix.
        self.log.info("got formresrou2x: %s", formresource)
        options = {
            'container_image': dockerimage,
            'resource_name': formresource,
            'resource_ram': resourceconfig['ram'],
            'resource_cpu': resourceconfig['cpu']
        }
        return options

    def start(self, image=None, extra_create_kwargs=None,
            extra_start_kwargs=None, extra_host_config=None):
        # container_prefix is used to construct container_name
        #self.container_prefix = self.user_options['container_prefix']

        # start the container
        return MarathonSpawner.start(
            self, app_image=self.user_options['container_image'],
                  resource_name=self.user_options['resource_name'],
                  resource_ram=self.user_options['resource_ram'], 
                  resource_cpu=self.user_options['resource_cpu']
        )
    
# http://jupyter.readthedocs.io/en/latest/development_guide/coding_style.html
# vim: set ai et ts=4 sw=4:
