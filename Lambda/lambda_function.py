import json
import boto3
from botocore.exceptions import ClientError

symptom_to_specialty_list = [
    {"chest pain":["cardiology", "gastroenterology", "pulmonology"]},
    {"shortness of breath": ["pulmonology", "cardiology", "hematology"]},
    {"joint pain": ["rheumatology", "infectious disease", "orthopedics"]},
    {"skin rash": ["dermatology", "allergy and immunology", "infectious disease"]},
    {"abdominal pain": ["gastroenterology", "obstetrics and gynecology", "hepatology", "general_surgery"]},
    {"frequent urination": ["urology", "endocrinology"]},
    {"vision loss": ["ophthalmology", "neurology"]},
    {"hearing loss": ["otolaryngology", "audiology"]},
    {"toothache": ["dentistry", "endodontics"]},
    {"anxiety": ["psychiatry", "psychology", "neurology", "cardiology"]},
    {"depression": ["psychiatry", "psychology", "endocrinology", "neurology"]},
    {"dizziness": ["neurology", "otolaryngology"]},
    {"back pain": ["orthopedics", "pain management", "neurology", "general_surgery"]},
    {"foot pain": ["podiatry", "orthopedics", "dermatology"]},
    {"allergies": ["allergy and immunology", "pulmonology"]},
    {"asthma": ["pulmonology", "immunology"]},
    {"high blood pressure": ["cardiology", "nephrology", "endocrinology"]},
    {"diarrhea": ["gastroenterology", "infectious disease", "colorectal_surgery"]},
    {"constipation": ["gastroenterology", "internal medicine", "colorectal_surgery", "general_surgery"]},
    {"insomnia": ["sleep medicine", "psychology"]},
    {"menstrual irregularities": ["gynecology", "reproductive endocrinology"]},
    {"erectile dysfunction": ["urology", "cardiology"]},
    {"infertility": ["reproductive endocrinology", "urology"]},
    {"incontinence": ["urology", "gynecology"]},
    {"hair loss": ["dermatology", "endocrinology", "hematology"]},
    {"vertigo": ["otolaryngology", "neurology"]},
    {"sinus congestion": ["otolaryngology", "allergy and immunology"]},
    {"tinnitus": ["otolaryngology", "audiology"]},
    {"nosebleeds": ["otolaryngology", "hematology"]},
    {"cough": ["pulmonology", "infectious disease"]},
    {"heartburn": ["gastroenterology", "cardiology"]},
    {"acid reflux": ["gastroenterology", "surgery"]},
    {"anemia": ["hematology", "gastroenterology"]},
    {"bruising": ["hematology", "dermatology"]},
    {"seizures": ["neurology", "epileptology"]},
    {"memory loss": ["neurology", "psychiatry"]},
    {"tremors": ["neurology", "movement disorders"]},
    {"swollen lymph nodes": ["hematology", "infectious disease"]},
    {"low libido": ["endocrinology", "urology"]},
    {"night sweats": ["internal medicine", "infectious disease"]},
    {"fever": ["infectious disease", "rheumatology", "oncology"]}
]

def lambda_handler(event, context):
    data_list = []
    for entry in symptom_to_specialty_list:
        record = {}
        record["symptom"] = list(entry.keys())[0]
        record["specialties"] = entry[list(entry.keys())[0]]
        data_list.append(record)

    insert_data(data_list)
    return

def insert_data(data_list, db=None, table='SymptomSpecialty'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response