## JSONIC: the decorator
class jsonic(object):
    
    """ Relies on Python 2.7-ish string-encoding semantics; makes a whoooole lot
        of assumptions about naming, additional installed, apps, you name it –
        Also, it’s absolutely horrid. I hereby place it in the public domain.
        
        Usage example:
        
            class MyModel(models.Model):
                
                @jsonic(
                    skip=[
                        'categories', 'images', 'aximage_set', 'axflashmorsel_set',
                        'tags', 'tagstring', 'color', 'colors', 'topsat', 'complement', 'inversecomplement',
                    ], include=[
                        'keyimage', 'flashmorsel',
                    ],
                )
                def json(self, **kwargs):
                    return kwargs.get('json', None)
        
        … would then allow, on an instance `my_model` of model class `MyModel`,
          to call the method:
        
            >>> my_model.json()
            (… gigantic Python – not JSON! – dictionary …)
        
        … which in an API view the dict, which would have keys and values from
          the instance that vaguely corresponded to all the stuff in the decorator
          params, would get encoded and stuck in a response.
        
        Actual production code written by me, circa 2008. Yep.
    """
    
    def __init__(self, *decorargs, **deckeywords):
        self.deckeywords = deckeywords
    
    def __call__(self, fn):
        def jsoner(obj, **kwargs):
            dic = {}
            key = None
            dictionary = None
            recurse_limit = 2
            thefields = obj._meta.get_all_field_names()
            kwargs.update(self.deckeywords) # ??
            
            recurse = kwargs.get('recurse', 0)
            incl = kwargs.get('include')
            sk = kwargs.get('skip')
            if incl:
                if type(incl) == type([]):
                    thefields.extend(incl)
                else:
                    thefields.append(incl)
            if sk:
                if type(sk) == type([]):
                    for skipper in sk:
                        if skipper in thefields:
                            thefields.remove(skipper)
                else:
                    if sk in thefields:
                        thefields.remove(sk)
            
            ## first vanilla fields
            for f in thefields:
                try:
                    dictionary = getattr(obj, "%s_set" % f)
                except AttributeError:
                    try:
                        dictionary = getattr(obj, f)
                    except AttributeError: pass
                    except ObjectDoesNotExist: pass
                    else:
                        key = str(f)
                except ObjectDoesNotExist: pass
                else:
                    key = "%s_set" % f
                
                if key:
                    if hasattr(dictionary, "__class__") and hasattr(dictionary, "all"):
                        if callable(dictionary.all):
                            if hasattr(dictionary.all(), "json"):
                                if recurse < recurse_limit:
                                    kwargs['recurse'] = recurse + 1
                                    dic[key] = dictionary.all().json(**kwargs)
                    elif hasattr(dictionary, "json"):
                        if recurse < recurse_limit:
                            kwargs['recurse'] = recurse + 1
                            dic[key] = dictionary.json(**kwargs)
                    else:
                        try:
                            theuni = dictionary.__str__()
                        except UnicodeEncodeError:
                            theuni = dictionary.encode('utf-8')
                        dic[key] = theuni
            
            ## now, do we have imagekit stuff in there?
            if hasattr(obj, "_ik") and hasattr(obj, obj._ik.image_field) and hasattr(getattr(obj, obj._ik.image_field), 'size') and if getattr(obj, obj._ik.image_field):
                for ik_accessor in [getattr(obj, s.access_as) for s in obj._ik.specs]:
                    key = ik_accessor.spec.access_as
                    dic[key] = {
                        'url': ik_accessor.url,
                        'width': ik_accessor.width,
                        'height': ik_accessor.height,
                    }
            return fn(obj, json=dic, **kwargs)
        return jsoner
