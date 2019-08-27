from rest_framework_json_api.renderers import JSONRenderer


class HackJSONAPIRenderer(JSONRenderer):
    """
    The drf-jsonapi package hardcodes a reference to the object PK, and ignores our choice of lookup field (slug)

    This method restores the ID we actually want to display to the world. See context:
    https://github.com/django-json-api/django-rest-framework-json-api/issues/155

    It's a pretty icky solution. Because the package we use ignores the serializer, this trick would need to be
        replicated if we ever add other types of data, eg, relationship fields.
    """
    @classmethod
    def build_json_resource_obj(cls, fields, resource, resource_instance, resource_name,
                                force_type_resolution=False):
        # Dear reader, I am as embarrassed by this as you are
        base = super().build_json_resource_obj(fields, resource, resource_instance, resource_name,
                                               force_type_resolution=False)

        base['id'] = resource_instance.slug
        return base
