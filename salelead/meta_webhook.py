# # # salelead/meta_webhook.py
# # from django.http import HttpResponse
# # from django.conf import settings
# # from django.views.decorators.csrf import csrf_exempt

# # @csrf_exempt
# # def meta_webhook(request):
# #     if request.method == "GET":
# #         if (
# #             request.GET.get("hub.mode") == "subscribe"
# #             and request.GET.get("hub.verify_token") == settings.META_WEBHOOK_VERIFY_TOKEN
# #         ):
# #             return HttpResponse(
# #                 request.GET.get("hub.challenge"),
# #                 content_type="text/plain",
# #                 status=200,
# #             )
# #         return HttpResponse("Invalid token", status=403)

# #     if request.method == "POST":
# #         return HttpResponse("EVENT_RECEIVED", status=200)

# #     return HttpResponse("Method not allowed", status=405)

# # salelead/meta_webhook.py

# import json
# import requests
# from django.http import HttpResponse
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt

# META_GRAPH = "https://graph.facebook.com/v24.0"

# @csrf_exempt
# def meta_webhook(request):

#     # 🔹 Verification (already correct)
#     if request.method == "GET":
#         if (
#             request.GET.get("hub.mode") == "subscribe"
#             and request.GET.get("hub.verify_token") == settings.META_WEBHOOK_VERIFY_TOKEN
#         ):
#             return HttpResponse(
#                 request.GET.get("hub.challenge"),
#                 content_type="text/plain",
#                 status=200,
#             )
#         return HttpResponse("Invalid token", status=403)

#     # 🔹 Lead event
#     if request.method == "POST":
#         payload = json.loads(request.body)
#         print("META PAYLOAD:", payload)

#         try:
#             entry = payload["entry"][0]
#             change = entry["changes"][0]
#             value = change["value"]

#             leadgen_id = value.get("leadgen_id")
#             page_id = value.get("page_id")

#             if not leadgen_id:
#                 return HttpResponse("No leadgen_id", status=200)

#             # 🔹 Fetch lead details from Meta
#             lead_url = f"{META_GRAPH}/{leadgen_id}"
#             params = {
#                 "access_token": settings.META_WEBHOOK_VERIFY_TOKEN,
#                 "fields": "created_time,ad_id,ad_name,form_id,field_data"
#             }

#             res = requests.get(lead_url, params=params)
#             lead_data = res.json()

#             print("LEAD DATA:", lead_data)

#             # 🔹 Send to your CRM ingest API
#             crm_url = f"{settings.BACKEND_BASE_URL}/api/sales/integrations/opportunities/META/"

#             requests.post(crm_url, json={
#                 "source": "META",
#                 "page_id": page_id,
#                 "leadgen_id": leadgen_id,
#                 "raw": lead_data
#             }, timeout=5)

#         except Exception as e:
#             print("META ERROR:", str(e))

#         return HttpResponse("EVENT_RECEIVED", status=200)

#     return HttpResponse("Method not allowed", status=405)


# # salelead/meta_webhook.py

# import json
# import requests
# from django.http import HttpResponse
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt

# from salelead.models import LeadOpportunity, LeadSourceSystem

# META_GRAPH = "https://graph.facebook.com/v24.0"


# @csrf_exempt
# def meta_webhook(request):

#     # ============================================================
#     # 🔹 META VERIFICATION (for Facebook Webhook setup)
#     # ============================================================
#     if request.method == "GET":
#         if (
#             request.GET.get("hub.mode") == "subscribe"
#             and request.GET.get("hub.verify_token") == settings.META_WEBHOOK_VERIFY_TOKEN
#         ):
#             return HttpResponse(
#                 request.GET.get("hub.challenge"),
#                 content_type="text/plain",
#                 status=200,
#             )
#         return HttpResponse("Invalid token", status=403)

#     # ============================================================
#     # 🔹 POST: META WEBHOOK + ZAPIER
#     # ============================================================
#     if request.method == "POST":
#         try:
#             payload = json.loads(request.body or "{}")
#             print("INCOMING PAYLOAD:", payload)

#             # ====================================================
#             # ✅ CASE 1: ZAPIER → CRM
#             # ====================================================
#             if payload.get("source") == "zapier":

#                 leadgen_id = (
#                     payload.get("external_id")
#                     or payload.get("leadgen_id")
#                     or payload.get("Lead Id")
#                     or payload.get("lead_id")
#                 )

#                 if not leadgen_id:
#                     print("❌ NO LEAD ID FOUND:", payload)
#                     return HttpResponse("No lead id", status=200)

#                 LeadOpportunity.objects.update_or_create(
#                     source_system=LeadSourceSystem.META,
#                     external_id=str(leadgen_id),
#                     defaults={
#                         "source_name": "META Lead Ads",
#                         "full_name": payload.get("Full Name") or payload.get("full_name", ""),
#                         "email": payload.get("Email") or payload.get("email", ""),
#                         "mobile_number": payload.get("Phone Number") or payload.get("mobile", ""),
#                         "raw_payload": payload,
#                     }
#                 )

#                 return HttpResponse("ZAPIER_LEAD_SAVED", status=200)


#             # ====================================================
#             # ✅ CASE 2: DIRECT META WEBHOOK
#             # ====================================================
#             entry = payload.get("entry", [{}])[0]
#             change = entry.get("changes", [{}])[0]
#             value = change.get("value", {})

#             leadgen_id = value.get("leadgen_id")
#             page_id = value.get("page_id")

#             if not leadgen_id:
#                 return HttpResponse("No leadgen_id", status=200)
            
#             # ====================================================
# # ✅ CASE 2: DIRECT META WEBHOOK (optional / future)
# # ====================================================
#             if not getattr(settings, "META_ACCESS_TOKEN", None):
#                 return HttpResponse("META_ACCESS_TOKEN_NOT_CONFIGURED", status=200)


#             # 🔹 Fetch full lead details from Meta
#             lead_url = f"{META_GRAPH}/{leadgen_id}"
#             params = {
#                 "access_token": settings.META_ACCESS_TOKEN,  # ✅ PAGE ACCESS TOKEN
#                 "fields": "created_time,ad_id,ad_name,form_id,field_data"
#             }

#             res = requests.get(lead_url, params=params, timeout=5)
#             lead_data = res.json()

#             # 🔹 Parse field_data
#             name = ""
#             email = ""
#             phone = ""

#             for field in lead_data.get("field_data", []):
#                 if field.get("name") == "full_name":
#                     name = field.get("values", [""])[0]
#                 elif field.get("name") == "email":
#                     email = field.get("values", [""])[0]
#                 elif field.get("name") in ["phone_number", "mobile_number"]:
#                     phone = field.get("values", [""])[0]

#             LeadOpportunity.objects.update_or_create(
#                 source_system=LeadSourceSystem.META,
#                 external_id=leadgen_id,
#                 defaults={
#                     "source_name": "META Lead Ads",
#                     "full_name": name,
#                     "email": email,
#                     "mobile_number": phone,
#                     "raw_payload": lead_data,
#                 }
#             )

#             return HttpResponse("META_LEAD_SAVED", status=200)

#         except Exception as e:
#             print("META WEBHOOK ERROR:", str(e))
#             return HttpResponse("ERROR", status=500)

#     return HttpResponse("Method not allowed", status=405)

# salelead/meta_webhook.py

import json
import requests
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from salelead.models import LeadOpportunity, LeadSourceSystem

META_GRAPH = "https://graph.facebook.com/v24.0"


@csrf_exempt
def meta_webhook(request):

    # ============================================================
    # 🔹 META VERIFICATION (for Facebook Webhook setup)
    # ============================================================
    if request.method == "GET":
        if (
            request.GET.get("hub.mode") == "subscribe"
            and request.GET.get("hub.verify_token") == settings.META_WEBHOOK_VERIFY_TOKEN
        ):
            return HttpResponse(
                request.GET.get("hub.challenge"),
                content_type="text/plain",
                status=200,
            )
        return HttpResponse("Invalid token", status=403)

    # ============================================================
    # 🔹 POST: META WEBHOOK + ZAPIER
    # ============================================================
    if request.method == "POST":
        try:
            payload = json.loads(request.body or "{}")
            print("INCOMING PAYLOAD:", payload)

            # ====================================================
            # ✅ CASE 1: ZAPIER → CRM
            # ====================================================
            # ================================
# ✅ CASE 1: ZAPIER → CRM
# ================================
            # ================================
# ✅ CASE 1: ZAPIER → CRM (FINAL)
# ================================
            if payload.get("source") == "zapier":

                leadgen_id = (
                    payload.get("external_id")
                    or payload.get("Lead Id")
                    or payload.get("lead_id")
                    or payload.get("id")
                )

                if not leadgen_id:
                    return HttpResponse("ZAPIER_NO_LEAD_ID", status=200)

                LeadOpportunity.objects.update_or_create(
                    source_system=LeadSourceSystem.META,
                    external_id=str(leadgen_id),
                    defaults={
                        "source_name": payload.get("Form Name", "META Lead Ads"),
                        "full_name": payload.get("Full Name", payload.get("full_name", "")),
                        "email": payload.get("Email", payload.get("email", "")),
                        "mobile_number": payload.get("Phone Number", payload.get("mobile", "")),
                        "raw_payload": payload,
                    }
                )

                return HttpResponse("ZAPIER_LEAD_SAVED", status=200)

            # ====================================================
            # ✅ CASE 2: DIRECT META WEBHOOK
            # ====================================================
            entry = payload.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})

            leadgen_id = value.get("leadgen_id")
            page_id = value.get("page_id")

            if not leadgen_id:
                return HttpResponse("No leadgen_id", status=200)
            
            # ====================================================
# ✅ CASE 2: DIRECT META WEBHOOK (optional / future)
# ====================================================
            if not getattr(settings, "META_ACCESS_TOKEN", None):
                return HttpResponse("META_ACCESS_TOKEN_NOT_CONFIGURED", status=200)


            # 🔹 Fetch full lead details from Meta
            lead_url = f"{META_GRAPH}/{leadgen_id}"
            params = {
                "access_token": settings.META_ACCESS_TOKEN,  # ✅ PAGE ACCESS TOKEN
                "fields": "created_time,ad_id,ad_name,form_id,field_data"
            }

            res = requests.get(lead_url, params=params, timeout=5)
            lead_data = res.json()

            # 🔹 Parse field_data
            name = ""
            email = ""
            phone = ""

            for field in lead_data.get("field_data", []):
                if field.get("name") == "full_name":
                    name = field.get("values", [""])[0]
                elif field.get("name") == "email":
                    email = field.get("values", [""])[0]
                elif field.get("name") in ["phone_number", "mobile_number"]:
                    phone = field.get("values", [""])[0]

            LeadOpportunity.objects.update_or_create(
                source_system=LeadSourceSystem.META,
                external_id=leadgen_id,
                defaults={
                    "source_name": "META Lead Ads",
                    "full_name": name,
                    "email": email,
                    "mobile_number": phone,
                    "raw_payload": lead_data,
                }
            )

            return HttpResponse("META_LEAD_SAVED", status=200)

        except Exception as e:
            print("META WEBHOOK ERROR:", str(e))
            return HttpResponse("ERROR", status=500)

    return HttpResponse("Method not allowed", status=405)