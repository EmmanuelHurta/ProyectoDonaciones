import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

def enviar_correo_brevo(destinatario, asunto, mensaje_html):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": destinatario}],
        sender={
            "email": settings.BREVO_SENDER_EMAIL,
            "name": settings.BREVO_SENDER_NAME
        },
        subject=asunto,
        html_content=mensaje_html
    )

    try:
        api_instance.send_transac_email(email)
        return True
    except ApiException as e:
        print(f"❌ Error enviando correo: {e}")
        return False


