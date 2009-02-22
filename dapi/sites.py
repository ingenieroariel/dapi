import re
from django import http, template
from dapi import ModelApi
from django.contrib.auth import authenticate, login
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy, ugettext as _
from django.views.decorators.cache import never_cache
from django.conf import settings


class ApiSite(object):
    def __init__(self, name=None):
        self._registry = {} # model_class class -> api_class instance
        # TODO Root path is used to calculate urls under the old root() method
        # in order to maintain backwards compatibility we are leaving that in
        # so root_path isn't needed, not sure what to do about this.
        self.root_path = 'admin/'
        if name is None:
            name = ''
        else:
            name += '_'
    def register(self, model_or_iterable, api_class=None, **options):  
          """
          Registers the given model(s) with the given api class.
            
          The model(s) should be Model classes, not
          instances.
  
          If an admin class isn't given, it will use ModelAdmin (the default
          admin options). If keyword arguments are given --
          e.g., list_display --
          they'll be applied as options to the admin class.
            
          If a model is already registered, this will raise
          AlreadyRegistered.
          """
         
          if not api_class:
              api_class = ModelApi

          if isinstance(model_or_iterable, ModelBase):
               model_or_iterable = [model_or_iterable]

          for model in model_or_iterable:
              if model in self._registry:
                  raise AlreadyRegistered('The model %s is already registered' % model.__name__)

              self._registry[model] = api_class(model, self)

    def unregister(self, model_or_iterable):
        """
        Unregisters the given model(s).
        
        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
                model_or_iterable = [model_or_iterable]
            for model in model_or_iterable:
                if model not in self._registry:
                    raise NotRegistered('The model %s is not registered' % model.__name__)
                del self._registry[model]
    def has_permission(self, request):
         """
         Returns True if the given HttpRequest has permission to
         *at least one* api method.
         """
         return request.user.is_authenticated() and request.user.is_staff

    def check_dependencies(self):
        """
        Check that all things needed to run the admin have been correctly installed.
          
        The default implementation checks that LogEntry, ContentType and the
        auth context processor are installed.
        """
        from django.contrib.contenttypes.models import ContentType

        if not ContentType._meta.installed:
            raise ImproperlyConfigured("Put 'django.contrib.contenttypes' in your INSTALLED_APPS
            setting in order to use dapi.")

        if 'django.core.context_processors.auth' not in settings.TEMPLATE_CONTEXT_PROCESSORS:
            raise ImproperlyConfigured("Put 'django.core.context_processors.auth' in your
                TEMPLATE_CONTEXT_PROCESSORS setting in order to use the
                admin application.")

        def api_view(self, view):
        """
        Decorator to create an "api view attached to this ``ApiSite``. This
        wraps the view and provides permission checking by calling
        ``self.has_permission``.
             
        You'll want to use this from within ``ApiSite.get_urls()``:
        class MyApiSite(ApiSite):
            def get_urls(self):
                from django.conf.urls.defaults import patterns, url
                urls = super(MyAdminSite, self).get_urls()
                urls += patterns('',
                     url(r'^my_view/$', self.protected_view(some_view))
                )
                return urls
        """
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                return self.login(request)
            return view(request, *args, **kwargs)
        return update_wrapper(inner, view)
        def get_urls(self):
            from django.conf.urls.defaults import patterns, url,include
           
            def wrap(view):
                def wrapper(*args, **kwargs):
                    return self.admin_view(view)(*args, **kwargs)
                return update_wrapper(wrapper, view)
            # Api-site-wide views.
            urlpatterns = patterns('',
            url(r'^$', 
                wrap(self.index),
                name='%sapi_index' % self.name),
            url(r'^r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                   'django.views.defaults.shortcut'),
            # Add in each model's views.
        for model, model_admin in self._registry.iteritems():
                 urlpatterns += patterns('',
                    url(r'^%s/%s/' % (model._meta.app_label, model._meta.module_name),
                        include(model_admin.urls))
                 )
            return urlpatterns
       
        def urls(self):
            return self.get_urls()
        urls = property(urls)
            
        def index(self, request, extra_context=None):
            """
            Displays the main api index page, which lists all of the installed
            apps that have been registered in this site.
            """
            app_dict = {}
            user = request.user
            for model, model_admin in self._registry.items():
               app_label = model._meta.app_label
               has_module_perms = user.has_module_perms(app_label)
                
               if has_module_perms:
                   perms = {
                       'add': model_admin.has_add_permission(request),
                       'change': model_admin.has_change_permission(request),
                       'delete': model_admin.has_delete_permission(request),
                   }
                   
                   # Check whether user has any perm for this module.
                   # If so, add the module to the model_list.
                   if True in perms.values():
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                            'perms': perms,
                        }
                        if app_label in app_dict:
                            app_dict[app_label]['models'].append(model_dict)
                        else:
                            app_dict[app_label] = {
                                'name': app_label.title(),
                                'app_url': app_label + '/',
                                'has_module_perms': has_module_perms,
                                'models': [model_dict],
                            }
            
            # Sort the apps alphabetically.
            app_list = app_dict.values()
 
            # This is not required but nice to have
            app_list.sort(lambda x, y: cmp(x['name'], y['name']))
            
            # Sort the models alphabetically within each app.
            for app in app_list:
                app['models'].sort(lambda x, y: cmp(x['name'], y['name']))
            
            context = {
                'title': _('Site api'),
                'app_list': app_list,
                'root_path': self.root_path,
            }
            context.update(extra_context or {})
            return render_to_response(self.index_template or 'api/index.html', context,
                context_instance=template.RequestContext(request)
            )
        index = never_cache(index)

    def app_index(self, request, app_label, extra_context=None):
        user = request.user
        has_module_perms = user.has_module_perms(app_label)
        app_dict = {}
        for model, model_admin in self._registry.items():
            if app_label == model._meta.app_label:
                if has_module_perms:
                    perms = {
                       'add': user.has_perm("%s.%s" % (app_label, model._meta.get_add_permission())),
                       'change': user.has_perm("%s.%s" % (app_label, model._meta.get_change_permission())),
                       'delete': user.has_perm("%s.%s" % (app_label, model._meta.get_delete_permission())),
                    }
                    # Check whether user has any perm for this module.
                    # If so, add the module to the model_list.
                    if True in perms.values():
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'api_url': '%s/' % model.__name__.lower(),
                            'perms': perms,
                        }
                        if app_dict:
                            app_dict['models'].append(model_dict),
                        else:
                            # First time around, now that we know there's
                            # something to display, add in the necessary meta
                            # information.
                            app_dict = {
                                'name': app_label.title(),
                                     'app_url': '',
                                     'has_module_perms': has_module_perms,
                                     'models': [model_dict],
                                 }
            if not app_dict:
                raise http.Http404('The requested api page does not exist.')
            # Sort the models alphabetically within each app.
            app_dict['models'].sort(lambda x, y: cmp(x['name'], y['name']))
            context = {
                'title': _('%s administration') % capfirst(app_label),
                'app_list': [app_dict],
                'root_path': self.root_path,
            }
            context.update(extra_context or {})
            return render_to_response(self.app_index_template or 'api/app_index.html', context,
                context_instance=template.RequestContext(request)
            )   

    
        def root(self, request, url): 
            """
            DEPRECATED. This function is the old way of handling URL resolution, and
            is deprecated in favor of real URL resolution -- see ``get_urls()``.
            
            This function still exists for backwards-compatibility; it will be
            removed in Django 1.3.
            """
            import warnings
            warnings.warn(
                "ApiSite.root() is deprecated; use include(api.site.urls) instead.",
                PendingDeprecationWarning
            )
           
            #
            # Again, remember that the following only exists for
            # backwards-compatibility. Any new URLs, changes to existing URLs, or
            # whatever need to be done up in get_urls(), above!
            #
            
            if request.method == 'GET' and not request.path.endswith('/'):
                return http.HttpResponseRedirect(request.path + '/')
           
            if settings.DEBUG:
                self.check_dependencies()
           
            # Figure out the admin base URL path and stash it for later use
            self.root_path = re.sub(re.escape(url) + '$', '', request.path)
           
            url = url.rstrip('/') # Trim trailing slash, if it exists.
           
            # The 'logout' view doesn't require that the person is logged in.
            
            # Check permission to continue or display login form.
            if not self.has_permission(request):
                return http.Http404("You are not authenticated, there is no api site for you")
             
            if url == '':
                return self.index(request)
            # URLs starting with 'r/' are for the "View on site" links.
            elif url.startswith('r/'):
                from django.contrib.contenttypes.views import shortcut
                return shortcut(request, *url.split('/')[1:])
            else:
                if '/' in url:
                    return self.model_page(request, *url.split('/', 2))
                else:
                    return self.app_index(request, url)
        def model_page(self, request, app_label, model_name, rest_of_url=None):
            """
            DEPRECATED. This is the old way of handling a model view on the api
            site; the new views should use get_urls(), above.
            """
            from django.db import models
            model = models.get_model(app_label, model_name)
            if model is None:
                raise http.Http404("App %r, model %r, not found." % (app_label, model_name))
            try:
                api_obj = self._registry[model]
            except KeyError:
                raise http.Http404("This model exists but has not been registered with the api site.")
            return admin_obj(request, rest_of_url)
        model_page = never_cache(model_page)   
    
    # This global object represents the default admin site, for the common case.
    # You can instantiate ApiSite in your own code to create a custom api site.
    site = ApiSite()
