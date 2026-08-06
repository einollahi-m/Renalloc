from django.urls import path

from . import api


app_name = "registry"

urlpatterns = [
    path("identifier-availability/", api.identifier_availability, name="identifier-availability"),
    path("options/", api.registry_options, name="options"),
    path("people/lookup/", api.person_lookup, name="person-lookup"),
    path("recipients/lookup/", api.recipient_lookup, name="recipient-lookup"),
    path("recipients/", api.recipients, name="recipients"),
    path("recipients/<uuid:person_id>/", api.recipient_detail, name="recipient-detail"),
    path("recipients/<uuid:person_id>/status/", api.recipient_status, name="recipient-status"),
    path("recipients/<uuid:person_id>/priority/", api.recipient_priority, name="recipient-priority"),
    path("recipients/<uuid:person_id>/matches/", api.patient_matches, name="patient-matches"),
    path("donors/", api.donors, name="donors"),
    path("donors/<uuid:person_id>/", api.donor_detail, name="donor-detail"),
    path("donors/<uuid:person_id>/status/", api.donor_status, name="donor-status"),
    path("donors/<uuid:person_id>/matches/", api.donor_matches, name="donor-matches"),
    path("people/<uuid:person_id>/hla/", api.person_hla, name="person-hla"),
    path("people/<uuid:person_id>/profile/", api.person_profile, name="person-profile"),
    path("people/<uuid:person_id>/labs/", api.lab_test_collection, name="lab-test-collection"),
    path(
        "people/<uuid:person_id>/labs/<uuid:test_id>/",
        api.lab_test_item,
        name="lab-test-item",
    ),
    path(
        "people/<uuid:person_id>/approvals/",
        api.approval_collection,
        name="approval-collection",
    ),
    path(
        "people/<uuid:person_id>/approvals/<int:approval_id>/",
        api.approval_item,
        name="approval-item",
    ),
    path(
        "people/<uuid:person_id>/cdc-pra/",
        api.cdc_pra_collection,
        name="cdc-pra-collection",
    ),
    path(
        "people/<uuid:person_id>/cdc-pra/<uuid:test_id>/",
        api.cdc_pra_item,
        name="cdc-pra-item",
    ),
    path(
        "people/<uuid:person_id>/anti-hla/",
        api.anti_hla_collection,
        name="anti-hla-collection",
    ),
    path(
        "people/<uuid:person_id>/anti-hla/<uuid:test_id>/",
        api.anti_hla_item,
        name="anti-hla-item",
    ),
    path("matching/preview/", api.matching_preview, name="matching-preview"),
    path(
        "matching/deceased-donor/",
        api.deceased_donor_matching,
        name="deceased-donor-matching",
    ),
    path("matching/runs/", api.matching_run, name="matching-run"),
    path("matching/enqueue/", api.matching_enqueue, name="matching-enqueue"),
    path("matching/proposals/", api.match_proposals, name="match-proposals"),
    path(
        "matching/proposals/<uuid:proposal_id>/consultation/",
        api.request_consultation,
        name="request-consultation",
    ),
    path(
        "matching/proposals/<uuid:proposal_id>/decision/",
        api.proposal_decision,
        name="proposal-decision",
    ),
    path("matching/crossmatches/", api.crossmatch_requests, name="crossmatch-requests"),
    path(
        "matching/crossmatches/<uuid:request_id>/",
        api.crossmatch_result,
        name="crossmatch-result",
    ),
    path("matching/policy/", api.allocation_policy, name="allocation-policy"),
    path("reports/national/", api.national_report, name="national-report"),
    path("notifications/", api.notifications, name="notifications"),
]
