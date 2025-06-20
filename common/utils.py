import pytz
from django.utils.translation import gettext_lazy as _


from django.http import HttpResponse
from rest_framework import status
import json

def ratelimit_error_handler(request, exception=None):
    """Return 429 instead of 403"""
    print("RATELIMIT_ERROR_HANDLER FUNCTION CALLED!")  
    print(f"Параметры: request={request}, exception={exception}")
    return HttpResponse(
        json.dumps({"detail": "Too many login attempts. Please try again later."}),
        content_type="application/json",
        status=status.HTTP_429_TOO_MANY_REQUESTS
    )

def jwt_payload_handler(user):
    """Custom payload handler
    Token encrypts the dictionary returned by this function, and can be
    decoded by rest_framework_jwt.utils.jwt_decode_handler
    """
    return {
        "id": user.pk,
        # 'name': user.name,
        "email": user.email,
        # "role": user.role,
        # "has_sales_access": user.has_sales_access,
        # "has_marketing_access": user.has_marketing_access,
        "file_prepend": user.file_prepend,
        "username": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        # "is_admin": user.is_admin,
        "is_staff": user.is_staff,
        # "date_joined"
    }


INDCHOICES = (
    ("ADVERTISING", "ADVERTISING"),
    ("AGRICULTURE", "AGRICULTURE"),
    ("APPAREL & ACCESSORIES", "APPAREL & ACCESSORIES"),
    ("AUTOMOTIVE", "AUTOMOTIVE"),
    ("BANKING", "BANKING"),
    ("BIOTECHNOLOGY", "BIOTECHNOLOGY"),
    ("BUILDING MATERIALS & EQUIPMENT", "BUILDING MATERIALS & EQUIPMENT"),
    ("CHEMICAL", "CHEMICAL"),
    ("COMPUTER", "COMPUTER"),
    ("EDUCATION", "EDUCATION"),
    ("ELECTRONICS", "ELECTRONICS"),
    ("ENERGY", "ENERGY"),
    ("ENTERTAINMENT & LEISURE", "ENTERTAINMENT & LEISURE"),
    ("FINANCE", "FINANCE"),
    ("FOOD & BEVERAGE", "FOOD & BEVERAGE"),
    ("GROCERY", "GROCERY"),
    ("HEALTHCARE", "HEALTHCARE"),
    ("INSURANCE", "INSURANCE"),
    ("LEGAL", "LEGAL"),
    ("MANUFACTURING", "MANUFACTURING"),
    ("PUBLISHING", "PUBLISHING"),
    ("REAL ESTATE", "REAL ESTATE"),
    ("SERVICE", "SERVICE"),
    ("SOFTWARE", "SOFTWARE"),
    ("SPORTS", "SPORTS"),
    ("TECHNOLOGY", "TECHNOLOGY"),
    ("TELECOMMUNICATIONS", "TELECOMMUNICATIONS"),
    ("TELEVISION", "TELEVISION"),
    ("TRANSPORTATION", "TRANSPORTATION"),
    ("VENTURE CAPITAL", "VENTURE CAPITAL"),
)

TYPECHOICES = (
    ("CUSTOMER", "CUSTOMER"),
    ("INVESTOR", "INVESTOR"),
    ("PARTNER", "PARTNER"),
    ("RESELLER", "RESELLER"),
)

ROLES = (
    ("ADMIN", "ADMIN"),
    ("USER", "USER"),
)

LEAD_STATUS = (
    ("assigned", "Assigned"),
    ("in process", "In Process"),
    ("converted", "Converted"),
    ("recycled", "Recycled"),
    ("closed", "Closed"),
)


LEAD_SOURCE = (
    ("call", "Call"),
    ("email", "Email"),
    ("existing customer", "Existing Customer"),
    ("partner", "Partner"),
    ("public relations", "Public Relations"),
    ("compaign", "Campaign"),
    ("other", "Other"),
)

STATUS_CHOICE = (
    ("New", "New"),
    ("Assigned", "Assigned"),
    ("Pending", "Pending"),
    ("Closed", "Closed"),
    ("Rejected", "Rejected"),
    ("Duplicate", "Duplicate"),
)

PRIORITY_CHOICE = (
    ("Low", "Low"),
    ("Normal", "Normal"),
    ("High", "High"),
    ("Urgent", "Urgent"),
)

CASE_TYPE = (("Question", "Question"), ("Incident", "Incident"), ("Problem", "Problem"))

STAGES = (
    ("QUALIFICATION", "QUALIFICATION"),
    ("NEEDS ANALYSIS", "NEEDS ANALYSIS"),
    ("VALUE PROPOSITION", "VALUE PROPOSITION"),
    ("ID.DECISION MAKERS", "ID.DECISION MAKERS"),
    ("PERCEPTION ANALYSIS", "PERCEPTION ANALYSIS"),
    ("PROPOSAL/PRICE QUOTE", "PROPOSAL/PRICE QUOTE"),
    ("NEGOTIATION/REVIEW", "NEGOTIATION/REVIEW"),
    ("CLOSED WON", "CLOSED WON"),
    ("CLOSED LOST", "CLOSED LOST"),
)

SOURCES = (
    ("NONE", "NONE"),
    ("CALL", "CALL"),
    ("EMAIL", " EMAIL"),
    ("EXISTING CUSTOMER", "EXISTING CUSTOMER"),
    ("PARTNER", "PARTNER"),
    ("PUBLIC RELATIONS", "PUBLIC RELATIONS"),
    ("CAMPAIGN", "CAMPAIGN"),
    ("WEBSITE", "WEBSITE"),
    ("OTHER", "OTHER"),
)

EVENT_PARENT_TYPE = ((10, "Account"), (13, "Lead"), (14, "Opportunity"), (11, "Case"))

EVENT_STATUS = (
    ("Planned", "Planned"),
    ("Held", "Held"),
    ("Not Held", "Not Held"),
    ("Not Started", "Not Started"),
    ("Started", "Started"),
    ("Completed", "Completed"),
    ("Canceled", "Canceled"),
    ("Deferred", "Deferred"),
)


COUNTRIES = (
    ("GB", _("United Kingdom")),
    ("AF", _("Afghanistan")),
    ("AX", _("Aland Islands")),
    ("AL", _("Albania")),
    ("DZ", _("Algeria")),
    ("AS", _("American Samoa")),
    ("AD", _("Andorra")),
    ("AO", _("Angola")),
    ("AI", _("Anguilla")),
    ("AQ", _("Antarctica")),
    ("AG", _("Antigua and Barbuda")),
    ("AR", _("Argentina")),
    ("AM", _("Armenia")),
    ("AW", _("Aruba")),
    ("AU", _("Australia")),
    ("AT", _("Austria")),
    ("AZ", _("Azerbaijan")),
    ("BS", _("Bahamas")),
    ("BH", _("Bahrain")),
    ("BD", _("Bangladesh")),
    ("BB", _("Barbados")),
    ("BY", _("Belarus")),
    ("BE", _("Belgium")),
    ("BZ", _("Belize")),
    ("BJ", _("Benin")),
    ("BM", _("Bermuda")),
    ("BT", _("Bhutan")),
    ("BO", _("Bolivia")),
    ("BA", _("Bosnia and Herzegovina")),
    ("BW", _("Botswana")),
    ("BV", _("Bouvet Island")),
    ("BR", _("Brazil")),
    ("IO", _("British Indian Ocean Territory")),
    ("BN", _("Brunei Darussalam")),
    ("BG", _("Bulgaria")),
    ("BF", _("Burkina Faso")),
    ("BI", _("Burundi")),
    ("KH", _("Cambodia")),
    ("CM", _("Cameroon")),
    ("CA", _("Canada")),
    ("CV", _("Cape Verde")),
    ("KY", _("Cayman Islands")),
    ("CF", _("Central African Republic")),
    ("TD", _("Chad")),
    ("CL", _("Chile")),
    ("CN", _("China")),
    ("CX", _("Christmas Island")),
    ("CC", _("Cocos (Keeling) Islands")),
    ("CO", _("Colombia")),
    ("KM", _("Comoros")),
    ("CG", _("Congo")),
    ("CD", _("Congo, The Democratic Republic of the")),
    ("CK", _("Cook Islands")),
    ("CR", _("Costa Rica")),
    ("CI", _("Cote d'Ivoire")),
    ("HR", _("Croatia")),
    ("CU", _("Cuba")),
    ("CY", _("Cyprus")),
    ("CZ", _("Czech Republic")),
    ("DK", _("Denmark")),
    ("DJ", _("Djibouti")),
    ("DM", _("Dominica")),
    ("DO", _("Dominican Republic")),
    ("EC", _("Ecuador")),
    ("EG", _("Egypt")),
    ("SV", _("El Salvador")),
    ("GQ", _("Equatorial Guinea")),
    ("ER", _("Eritrea")),
    ("EE", _("Estonia")),
    ("ET", _("Ethiopia")),
    ("FK", _("Falkland Islands (Malvinas)")),
    ("FO", _("Faroe Islands")),
    ("FJ", _("Fiji")),
    ("FI", _("Finland")),
    ("FR", _("France")),
    ("GF", _("French Guiana")),
    ("PF", _("French Polynesia")),
    ("TF", _("French Southern Territories")),
    ("GA", _("Gabon")),
    ("GM", _("Gambia")),
    ("GE", _("Georgia")),
    ("DE", _("Germany")),
    ("GH", _("Ghana")),
    ("GI", _("Gibraltar")),
    ("GR", _("Greece")),
    ("GL", _("Greenland")),
    ("GD", _("Grenada")),
    ("GP", _("Guadeloupe")),
    ("GU", _("Guam")),
    ("GT", _("Guatemala")),
    ("GG", _("Guernsey")),
    ("GN", _("Guinea")),
    ("GW", _("Guinea-Bissau")),
    ("GY", _("Guyana")),
    ("HT", _("Haiti")),
    ("HM", _("Heard Island and McDonald Islands")),
    ("VA", _("Holy See (Vatican City State)")),
    ("HN", _("Honduras")),
    ("HK", _("Hong Kong")),
    ("HU", _("Hungary")),
    ("IS", _("Iceland")),
    ("IN", _("India")),
    ("ID", _("Indonesia")),
    ("IR", _("Iran, Islamic Republic of")),
    ("IQ", _("Iraq")),
    ("IE", _("Ireland")),
    ("IM", _("Isle of Man")),
    ("IL", _("Israel")),
    ("IT", _("Italy")),
    ("JM", _("Jamaica")),
    ("JP", _("Japan")),
    ("JE", _("Jersey")),
    ("JO", _("Jordan")),
    ("KZ", _("Kazakhstan")),
    ("KE", _("Kenya")),
    ("KI", _("Kiribati")),
    ("KP", _("Korea, Democratic People's Republic of")),
    ("KR", _("Korea, Republic of")),
    ("KW", _("Kuwait")),
    ("KG", _("Kyrgyzstan")),
    ("LA", _("Lao People's Democratic Republic")),
    ("LV", _("Latvia")),
    ("LB", _("Lebanon")),
    ("LS", _("Lesotho")),
    ("LR", _("Liberia")),
    ("LY", _("Libyan Arab Jamahiriya")),
    ("LI", _("Liechtenstein")),
    ("LT", _("Lithuania")),
    ("LU", _("Luxembourg")),
    ("MO", _("Macao")),
    ("MK", _("Macedonia, The Former Yugoslav Republic of")),
    ("MG", _("Madagascar")),
    ("MW", _("Malawi")),
    ("MY", _("Malaysia")),
    ("MV", _("Maldives")),
    ("ML", _("Mali")),
    ("MT", _("Malta")),
    ("MH", _("Marshall Islands")),
    ("MQ", _("Martinique")),
    ("MR", _("Mauritania")),
    ("MU", _("Mauritius")),
    ("YT", _("Mayotte")),
    ("MX", _("Mexico")),
    ("FM", _("Micronesia, Federated States of")),
    ("MD", _("Moldova")),
    ("MC", _("Monaco")),
    ("MN", _("Mongolia")),
    ("ME", _("Montenegro")),
    ("MS", _("Montserrat")),
    ("MA", _("Morocco")),
    ("MZ", _("Mozambique")),
    ("MM", _("Myanmar")),
    ("NA", _("Namibia")),
    ("NR", _("Nauru")),
    ("NP", _("Nepal")),
    ("NL", _("Netherlands")),
    ("AN", _("Netherlands Antilles")),
    ("NC", _("New Caledonia")),
    ("NZ", _("New Zealand")),
    ("NI", _("Nicaragua")),
    ("NE", _("Niger")),
    ("NG", _("Nigeria")),
    ("NU", _("Niue")),
    ("NF", _("Norfolk Island")),
    ("MP", _("Northern Mariana Islands")),
    ("NO", _("Norway")),
    ("OM", _("Oman")),
    ("PK", _("Pakistan")),
    ("PW", _("Palau")),
    ("PS", _("Palestinian Territory, Occupied")),
    ("PA", _("Panama")),
    ("PG", _("Papua New Guinea")),
    ("PY", _("Paraguay")),
    ("PE", _("Peru")),
    ("PH", _("Philippines")),
    ("PN", _("Pitcairn")),
    ("PL", _("Poland")),
    ("PT", _("Portugal")),
    ("PR", _("Puerto Rico")),
    ("QA", _("Qatar")),
    ("RE", _("Reunion")),
    ("RO", _("Romania")),
    ("RU", _("Russian Federation")),
    ("RW", _("Rwanda")),
    ("BL", _("Saint Barthelemy")),
    ("SH", _("Saint Helena")),
    ("KN", _("Saint Kitts and Nevis")),
    ("LC", _("Saint Lucia")),
    ("MF", _("Saint Martin")),
    ("PM", _("Saint Pierre and Miquelon")),
    ("VC", _("Saint Vincent and the Grenadines")),
    ("WS", _("Samoa")),
    ("SM", _("San Marino")),
    ("ST", _("Sao Tome and Principe")),
    ("SA", _("Saudi Arabia")),
    ("SN", _("Senegal")),
    ("RS", _("Serbia")),
    ("SC", _("Seychelles")),
    ("SL", _("Sierra Leone")),
    ("SG", _("Singapore")),
    ("SK", _("Slovakia")),
    ("SI", _("Slovenia")),
    ("SB", _("Solomon Islands")),
    ("SO", _("Somalia")),
    ("ZA", _("South Africa")),
    ("GS", _("South Georgia and the South Sandwich Islands")),
    ("ES", _("Spain")),
    ("LK", _("Sri Lanka")),
    ("SD", _("Sudan")),
    ("SR", _("Suriname")),
    ("SJ", _("Svalbard and Jan Mayen")),
    ("SZ", _("Swaziland")),
    ("SE", _("Sweden")),
    ("CH", _("Switzerland")),
    ("SY", _("Syrian Arab Republic")),
    ("TW", _("Taiwan, Province of China")),
    ("TJ", _("Tajikistan")),
    ("TZ", _("Tanzania, United Republic of")),
    ("TH", _("Thailand")),
    ("TL", _("Timor-Leste")),
    ("TG", _("Togo")),
    ("TK", _("Tokelau")),
    ("TO", _("Tonga")),
    ("TT", _("Trinidad and Tobago")),
    ("TN", _("Tunisia")),
    ("TR", _("Turkey")),
    ("TM", _("Turkmenistan")),
    ("TC", _("Turks and Caicos Islands")),
    ("TV", _("Tuvalu")),
    ("UG", _("Uganda")),
    ("UA", _("Ukraine")),
    ("AE", _("United Arab Emirates")),
    ("US", _("United States")),
    ("UM", _("United States Minor Outlying Islands")),
    ("UY", _("Uruguay")),
    ("UZ", _("Uzbekistan")),
    ("VU", _("Vanuatu")),
    ("VE", _("Venezuela")),
    ("VN", _("Viet Nam")),
    ("VG", _("Virgin Islands, British")),
    ("VI", _("Virgin Islands, U.S.")),
    ("WF", _("Wallis and Futuna")),
    ("EH", _("Western Sahara")),
    ("YE", _("Yemen")),
    ("ZM", _("Zambia")),
    ("ZW", _("Zimbabwe")),
)

CURRENCY_CODES = (
    ("AED", _("AED, Dirham")),
    ("AFN", _("AFN, Afghani")),
    ("ALL", _("ALL, Lek")),
    ("AMD", _("AMD, Dram")),
    ("ANG", _("ANG, Guilder")),
    ("AOA", _("AOA, Kwanza")),
    ("ARS", _("ARS, Peso")),
    ("AUD", _("AUD, Dollar")),
    ("AWG", _("AWG, Guilder")),
    ("AZN", _("AZN, Manat")),
    ("BAM", _("BAM, Marka")),
    ("BBD", _("BBD, Dollar")),
    ("BDT", _("BDT, Taka")),
    ("BGN", _("BGN, Lev")),
    ("BHD", _("BHD, Dinar")),
    ("BIF", _("BIF, Franc")),
    ("BMD", _("BMD, Dollar")),
    ("BND", _("BND, Dollar")),
    ("BOB", _("BOB, Boliviano")),
    ("BRL", _("BRL, Real")),
    ("BSD", _("BSD, Dollar")),
    ("BTN", _("BTN, Ngultrum")),
    ("BWP", _("BWP, Pula")),
    ("BYR", _("BYR, Ruble")),
    ("BZD", _("BZD, Dollar")),
    ("CAD", _("CAD, Dollar")),
    ("CDF", _("CDF, Franc")),
    ("CHF", _("CHF, Franc")),
    ("CLP", _("CLP, Peso")),
    ("CNY", _("CNY, Yuan Renminbi")),
    ("COP", _("COP, Peso")),
    ("CRC", _("CRC, Colon")),
    ("CUP", _("CUP, Peso")),
    ("CVE", _("CVE, Escudo")),
    ("CZK", _("CZK, Koruna")),
    ("DJF", _("DJF, Franc")),
    ("DKK", _("DKK, Krone")),
    ("DOP", _("DOP, Peso")),
    ("DZD", _("DZD, Dinar")),
    ("EGP", _("EGP, Pound")),
    ("ERN", _("ERN, Nakfa")),
    ("ETB", _("ETB, Birr")),
    ("EUR", _("EUR, Euro")),
    ("FJD", _("FJD, Dollar")),
    ("FKP", _("FKP, Pound")),
    ("GBP", _("GBP, Pound")),
    ("GEL", _("GEL, Lari")),
    ("GHS", _("GHS, Cedi")),
    ("GIP", _("GIP, Pound")),
    ("GMD", _("GMD, Dalasi")),
    ("GNF", _("GNF, Franc")),
    ("GTQ", _("GTQ, Quetzal")),
    ("GYD", _("GYD, Dollar")),
    ("HKD", _("HKD, Dollar")),
    ("HNL", _("HNL, Lempira")),
    ("HRK", _("HRK, Kuna")),
    ("HTG", _("HTG, Gourde")),
    ("HUF", _("HUF, Forint")),
    ("IDR", _("IDR, Rupiah")),
    ("ILS", _("ILS, Shekel")),
    ("INR", _("INR, Rupee")),
    ("IQD", _("IQD, Dinar")),
    ("IRR", _("IRR, Rial")),
    ("ISK", _("ISK, Krona")),
    ("JMD", _("JMD, Dollar")),
    ("JOD", _("JOD, Dinar")),
    ("JPY", _("JPY, Yen")),
    ("KES", _("KES, Shilling")),
    ("KGS", _("KGS, Som")),
    ("KHR", _("KHR, Riels")),
    ("KMF", _("KMF, Franc")),
    ("KPW", _("KPW, Won")),
    ("KRW", _("KRW, Won")),
    ("KWD", _("KWD, Dinar")),
    ("KYD", _("KYD, Dollar")),
    ("KZT", _("KZT, Tenge")),
    ("LAK", _("LAK, Kip")),
    ("LBP", _("LBP, Pound")),
    ("LKR", _("LKR, Rupee")),
    ("LRD", _("LRD, Dollar")),
    ("LSL", _("LSL, Loti")),
    ("LTL", _("LTL, Litas")),
    ("LVL", _("LVL, Lat")),
    ("LYD", _("LYD, Dinar")),
    ("MAD", _("MAD, Dirham")),
    ("MDL", _("MDL, Leu")),
    ("MGA", _("MGA, Ariary")),
    ("MKD", _("MKD, Denar")),
    ("MMK", _("MMK, Kyat")),
    ("MNT", _("MNT, Tugrik")),
    ("MOP", _("MOP, Pataca")),
    ("MRO", _("MRO, Ouguiya")),
    ("MUR", _("MUR, Rupee")),
    ("MVR", _("MVR, Rufiyaa")),
    ("MWK", _("MWK, Kwacha")),
    ("MXN", _("MXN, Peso")),
    ("MYR", _("MYR, Ringgit")),
    ("MZN", _("MZN, Metical")),
    ("NAD", _("NAD, Dollar")),
    ("NGN", _("NGN, Naira")),
    ("NIO", _("NIO, Cordoba")),
    ("NOK", _("NOK, Krone")),
    ("NPR", _("NPR, Rupee")),
    ("NZD", _("NZD, Dollar")),
    ("OMR", _("OMR, Rial")),
    ("PAB", _("PAB, Balboa")),
    ("PEN", _("PEN, Sol")),
    ("PGK", _("PGK, Kina")),
    ("PHP", _("PHP, Peso")),
    ("PKR", _("PKR, Rupee")),
    ("PLN", _("PLN, Zloty")),
    ("PYG", _("PYG, Guarani")),
    ("QAR", _("QAR, Rial")),
    ("RON", _("RON, Leu")),
    ("RSD", _("RSD, Dinar")),
    ("RUB", _("RUB, Ruble")),
    ("RWF", _("RWF, Franc")),
    ("SAR", _("SAR, Rial")),
    ("SBD", _("SBD, Dollar")),
    ("SCR", _("SCR, Rupee")),
    ("SDG", _("SDG, Pound")),
    ("SEK", _("SEK, Krona")),
    ("SGD", _("SGD, Dollar")),
    ("SHP", _("SHP, Pound")),
    ("SLL", _("SLL, Leone")),
    ("SOS", _("SOS, Shilling")),
    ("SRD", _("SRD, Dollar")),
    ("SSP", _("SSP, Pound")),
    ("STD", _("STD, Dobra")),
    ("SYP", _("SYP, Pound")),
    ("SZL", _("SZL, Lilangeni")),
    ("THB", _("THB, Baht")),
    ("TJS", _("TJS, Somoni")),
    ("TMT", _("TMT, Manat")),
    ("TND", _("TND, Dinar")),
    ("TOP", _("TOP, Paanga")),
    ("TRY", _("TRY, Lira")),
    ("TTD", _("TTD, Dollar")),
    ("TWD", _("TWD, Dollar")),
    ("TZS", _("TZS, Shilling")),
    ("UAH", _("UAH, Hryvnia")),
    ("UGX", _("UGX, Shilling")),
    ("USD", _("$, Dollar")),
    ("UYU", _("UYU, Peso")),
    ("UZS", _("UZS, Som")),
    ("VEF", _("VEF, Bolivar")),
    ("VND", _("VND, Dong")),
    ("VUV", _("VUV, Vatu")),
    ("WST", _("WST, Tala")),
    ("XAF", _("XAF, Franc")),
    ("XCD", _("XCD, Dollar")),
    ("XOF", _("XOF, Franc")),
    ("XPF", _("XPF, Franc")),
    ("YER", _("YER, Rial")),
    ("ZAR", _("ZAR, Rand")),
    ("ZMK", _("ZMK, Kwacha")),
    ("ZWL", _("ZWL, Dollar")),
)


def return_complete_address(self):
    address = ""
    if self.address_line:
        address += self.address_line
    if self.street:
        if address:
            address += ", " + self.street
        else:
            address += self.street
    if self.city:
        if address:
            address += ", " + self.city
        else:
            address += self.city
    if self.state:
        if address:
            address += ", " + self.state
        else:
            address += self.state
    if self.postcode:
        if address:
            address += ", " + self.postcode
        else:
            address += self.postcode
    if self.country:
        if address:
            address += ", " + self.get_country_display()
        else:
            address += self.get_country_display()
    return address


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def convert_to_custom_timezone(custom_date, custom_timezone, to_utc=False):
    user_time_zone = pytz.timezone(custom_timezone)
    if to_utc:
        custom_date = user_time_zone.localize(custom_date.replace(tzinfo=None))
        user_time_zone = pytz.UTC
    return custom_date.astimezone(user_time_zone)


def append_str_to(append_to: str, *args, sep=", ", **kwargs):
    """Concatenate to a string.
    Args:
        append_to(str): The string to append to.
        args(list): list of string characters to concatenate.
        sep(str): Seperator to use between concatenated strings.
        kwargs(dict): Mapping of variables with intended string values.
    Returns:
        str, joined strings seperated
    """
    append_to = append_to or ""
    result_list = [append_to] + list(args) + list(kwargs.values())
    data = False
    for item in result_list:
        if item:
            data = True
            break
    return f"{sep}".join(filter(len, result_list)) if data else ""
