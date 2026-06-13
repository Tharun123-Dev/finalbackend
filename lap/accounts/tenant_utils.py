DEFAULT_TENANT_CODE = 'default'


def get_tenant_id(user_or_request):
    user = getattr(user_or_request, 'user', user_or_request)
    tenant_id = getattr(user, 'tenant_id', None) or DEFAULT_TENANT_CODE
    return str(tenant_id).strip()[:64] or DEFAULT_TENANT_CODE
