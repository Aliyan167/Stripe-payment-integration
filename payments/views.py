import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from .models import Payment
import json
stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    return render(request, 'home.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    })


def success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return HttpResponse("No session ID", status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_email = session['customer_details']['email']
        payment_intent = session['payment_intent']
        amount = session['amount_total']

        # Avoid duplicate entries
        if not Payment.objects.filter(stripe_payment_intent=payment_intent).exists():
            Payment.objects.create(
                stripe_payment_intent=payment_intent,
                email=customer_email,
                amount=amount
            )
    except Exception as e:
        return HttpResponse(f"Error retrieving session: {str(e)}", status=400)

    return render(request, 'success.html')


def cancel(request):
    return render(request, 'cancel.html')

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            product_name = data.get('product_name', 'Unnamed Product')
            amount = int(data.get('amount', 0))  # in cents
            quantity = int(data.get('quantity', 1))

            if amount <= 0 or quantity <= 0:
                return JsonResponse({'error': 'Invalid amount or quantity'}, status=400)

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product_name,
                        },
                        'unit_amount': amount,
                    },
                    'quantity': quantity,
                }],
                mode='payment',
                success_url='http://localhost:8000/success/?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:8000/cancel/',
            )
            return JsonResponse({'id': session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=400)


@csrf_exempt
def stripe_webhook(request):
    if request.method != 'POST':
        return HttpResponse("Webhook endpoint expects POST", status=200)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        Payment.objects.create(
            stripe_payment_intent=session.get('payment_intent'),
            email=session['customer_details']['email'],
            amount=session['amount_total'] / 100
        )

    return HttpResponse(status=200)
