import requests

from django import forms
from crispy_forms.layout import Layout, Div, Fieldset
from astropy.time import Time, TimezoneInfo
import datetime

from tom_alerts.alerts import GenericQueryForm, GenericBroker, GenericAlert
from tom_targets.models import Target

ALERCE_URL = "https://dev.alerce.online"
ALERCE_SEARCH_URL = "https://dev.api.alerce.online/objects"
ALERCE_OBJ_URL = "https://dev.api.alerce.online/objects/%s"
ALERCE_CLASSIFIERS_URL = "https://dev.api.alerce.online/classifiers"

SORT_CHOICES = [
    ("ndet", "Number Of Epochs"),
    ("lastmjd", "Last Detection"),
    ("probability", "Class Probability"),
]

PAGES_CHOICES = [(i, i) for i in [1, 5, 10, 15]]

RECORDS_CHOICES = [(i, i) for i in [20, 100, 500]]


class ALeRCEQueryForm(GenericQueryForm):

    lc_classifier_classes = []
    stamp_classifier_classes = []
    lc_classifier_version_default = "bulk_0.0.1"
    stamp_classifier_version_default = "bulk_0.0.1"

    nobs__gt = forms.IntegerField(
        required=False,
        label="Detections Lower",
        widget=forms.TextInput(attrs={"placeholder": "Min number of epochs"}),
    )
    nobs__lt = forms.IntegerField(
        required=False,
        label="Detections Upper",
        widget=forms.TextInput(attrs={"placeholder": "Max number of epochs"}),
    )
    lc_classifier_class = forms.ChoiceField(
        required=False,
        label="Light Curve Classifier Class",
        choices=lc_classifier_classes,
    )
    stamp_classifier_class = forms.ChoiceField(
        required=False,
        label="Stamp Classifier Class",
        choices=stamp_classifier_classes,
    )
    stamp_classifier_version = forms.CharField(disabled=True, initial=stamp_classifier_version_default)
    lc_classifier_version = forms.CharField(disabled=True, initial=lc_classifier_version_default)
    probability = forms.FloatField(required=False, label="Class minimum probability")
    ra = forms.IntegerField(
        required=False,
        label="RA",
        widget=forms.TextInput(attrs={"placeholder": "RA (Degrees)"}),
    )
    dec = forms.IntegerField(
        required=False,
        label="Dec",
        widget=forms.TextInput(attrs={"placeholder": "Dec (Degrees)"}),
    )
    sr = forms.IntegerField(
        required=False,
        label="Search Radius",
        widget=forms.TextInput(attrs={"placeholder": "SR (Degrees)"}),
    )
    mjd__gt = forms.FloatField(
        required=False,
        label="Min date of first detection ",
        widget=forms.TextInput(attrs={"placeholder": "Date (MJD)"}),
    )
    mjd__lt = forms.FloatField(
        required=False,
        label="Max date of first detection",
        widget=forms.TextInput(attrs={"placeholder": "Date (MJD)"}),
    )
    relative_mjd__gt = forms.FloatField(
        required=False,
        label="Relative date of object discovery.",
        widget=forms.TextInput(attrs={"placeholder": "Hours"}),
    )
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, label="Sort By")
    max_pages = forms.TypedChoiceField(
        choices=PAGES_CHOICES, required=False, label="Max Number of Pages"
    )
    records = forms.ChoiceField(
        choices=RECORDS_CHOICES, required=False, label="Records per page"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        response = requests.get(ALERCE_CLASSIFIERS_URL)
        response.raise_for_status()
        parsed = response.json()
        for c in parsed:
            if (
                c["classifier_name"] == "lc_classifier"
                and c["classifier_version"] == self.lc_classifier_version_default
            ):
                self.lc_classifier_classes = [
                    (cl, cl) for cl in c["classes"]
                ]
            if (
                c["classifier_name"] == "stamp_classifier"
                and c["classifier_version"] == self.stamp_classifier_version_default
            ):
                self.stamp_classifier_classes = [
                    (cl, cl) for cl in c["classes"]
                ]

        self.lc_classifier_classes.insert(0, (None, ""))
        self.stamp_classifier_classes.insert(0, (None, ""))

        self.fields["lc_classifier_class"].choices = self.lc_classifier_classes
        self.fields["stamp_classifier_class"].choices = self.stamp_classifier_classes

        self.helper.layout = Layout(
            self.common_layout,
            Fieldset(
                "Number of Epochs",
                Div(
                    Div(
                        "nobs__gt",
                        css_class="col",
                    ),
                    Div(
                        "nobs__lt",
                        css_class="col",
                    ),
                    css_class="form-row",
                ),
            ),
            Fieldset(
                "Classification Filters",
                Div(
                    Div("lc_classifier_class", css_class="col"),
                    Div("stamp_classifier_class", css_class="col"),
                    Div(
                        "probability",
                        css_class="col",
                    ),
                    css_class="form-row",
                ),
                Div(
                    Div("lc_classifier_version", css_class="col"),
                    Div("stamp_classifier_version", css_class="col"),
                    css_class="form-row",
                )
            ),
            Fieldset(
                "Location Filters",
                Div(
                    Div("ra", css_class="col"),
                    Div("dec", css_class="col"),
                    Div("sr", css_class="col"),
                    css_class="form-row",
                ),
            ),
            Fieldset(
                "Time Filters",
                Div(
                    Fieldset(
                        "Relative time",
                        Div(
                            "relative_mjd__gt",
                            css_class="col",
                        ),
                        css_class="col",
                    ),
                    Fieldset(
                        "Absolute time",
                        Div(
                            Div(
                                "mjd__gt",
                                css_class="col",
                            ),
                            Div(
                                "mjd__lt",
                                css_class="col",
                            ),
                            css_class="form-row",
                        ),
                    ),
                    css_class="form-row",
                ),
            ),
            Fieldset(
                "General Parameters",
                Div(
                    Div("sort_by", css_class="col"),
                    Div("records", css_class="col"),
                    Div("max_pages", css_class="col"),
                    css_class="form-row",
                ),
            ),
        )


class ALeRCEBroker(GenericBroker):
    name = "ALeRCE"
    form = ALeRCEQueryForm

    def _fetch_alerts_payload(self, parameters):
        payload = {
            "page": parameters.get("page", 1),
            "page_size": int(parameters.get("records", 20)),
            "order_by": parameters.get("sort_by"),
            "count": "true",
            "order_mode": "DESC"
        }
        if any(
            [
                parameters["nobs__gt"],
                parameters["nobs__lt"],
                parameters["lc_classifier_class"],
                parameters["stamp_classifier_class"],
                parameters["probability"],
            ]
        ):
            if any([parameters["nobs__gt"], parameters["nobs__lt"]]):
                payload["ndet"] = []
                if parameters["nobs__gt"]:
                    payload["ndet"].append(parameters["nobs__gt"])
                if parameters["nobs__lt"]:
                    if len(payload["ndet"]) == 0:
                        payload["ndet"].append(1)
                    payload["ndet"].append(parameters["nobs__lt"])
            if parameters["lc_classifier_class"]:
                payload["classifier"] = "lc_classifier"
                payload["classifier_version"] = parameters["lc_classifier_version"]
                payload["class"] = parameters["lc_classifier_class"]
            if parameters["stamp_classifier_class"]:
                payload["classifier"] = "stamp_classifier"
                payload["classifier_version"] = parameters["stamp_classifier_version"]
                payload["class"] = parameters["stamp_classifier_class"]
            if parameters["probability"]:
                payload["probability"] = parameters["probability"]

        if all([parameters["ra"], parameters["dec"], parameters["sr"]]):
            if parameters["ra"]:
                payload["ra"] = parameters["ra"]
            if parameters["dec"]:
                payload["dec"] = parameters["dec"]
            if parameters["sr"]:
                payload["radius"] = parameters["sr"]

        if any(
            [
                parameters["mjd__gt"],
                parameters["mjd__lt"],
                parameters["relative_mjd__gt"],
            ]
        ):
            payload["firstmjd"] = []
            if parameters["mjd__gt"]:
                payload["firstmjd"].append(parameters["mjd__gt"])
            elif parameters["relative_mjd__gt"]:
                now = datetime.datetime.utcnow()
                relative = now - datetime.timedelta(
                    hours=parameters["relative_mjd__gt"]
                )
                relative_astro = Time(relative)
                payload["firstmjd"].append(relative_astro.mjd)

            if parameters["mjd__lt"]:
                if len(payload["firstmjd"]) == 0:
                    payload["firstmjd"].append(0)
                payload["firstmjd"].append(parameters["mjd__lt"])
        return payload

    def fetch_alerts(self, parameters):
        payload = self._fetch_alerts_payload(parameters)
        response = requests.get(ALERCE_SEARCH_URL, params=payload)
        response.raise_for_status()
        parsed = response.json()
        alerts = [alert_data for alert_data in parsed["items"]]
        if parsed["has_next"] and parsed["page"] != int(parameters["max_pages"]):
            print("page", parsed["page"])
            print("has_next", parsed["has_next"])
            print("max_pages", parameters["max_pages"])
            parameters["page"] = parsed.get("next")
            alerts += self.fetch_alerts(parameters)
        return iter(alerts)

    def fetch_alert(self, id):
        response = requests.post(ALERCE_OBJ_URL % id)
        response.raise_for_status()
        return response.json()

    def to_target(self, alert):
        return Target.objects.create(
            name=alert["oid"], type="SIDEREAL", ra=alert["meanra"], dec=alert["meandec"]
        )

    def to_generic_alert(self, alert):
        if alert["lastmjd"]:
            timestamp = Time(alert["lastmjd"], format="mjd", scale="utc").to_datetime(
                timezone=TimezoneInfo()
            )
        else:
            timestamp = ""
        url = "{0}/{1}/{2}".format(ALERCE_URL, "object", alert["oid"])

        return GenericAlert(
            timestamp=timestamp,
            url=url,
            id=alert["oid"],
            name=alert["oid"],
            ra=alert["meanra"],
            dec=alert["meandec"],
            mag=alert["g_r_max_corr"],
            score=alert["probability"],
        )
