def currency(request):
    """Inject the user's preferred currency symbol into every template context."""
    symbol = 'FCFA'
    if request.user.is_authenticated:
        try:
            symbol = request.user.profile.currency
        except Exception:
            symbol = 'FCFA'
    return {'currency': symbol}
