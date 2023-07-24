import frappe
from frappe.model.document import Document
from datetime import datetime
import requests
import json
import os
import re


class BPS(Document):
    pattern = r"^[a-zA-Z]*$"
    details_dict = {}
    patient_id = None

    def get_json_response(self, url):
        if self.authentication_key == "****" or self.authentication_key == "":
            frappe.throw("Authentication key is missing or invalid.")

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.authentication_key,
        }
        response = requests.get(url, headers=headers)

        return (response.status_code, response.json())

    def send_post_request(self, url):
        return requests.post(url)

    def encode(self, name, value, operator=None):
        if operator == "or":
            return "%2C" + name + "%3D%3D" + value
        elif operator == "and":
            return "%3B" + name + "%3D%3D" + value

        return name + "%3D%3D" + value

    def _or(self, name, value):
        return self.encode(name, value, "or")

    def _and(self, name, value):
        return self.encode(name, value, "and")

    def replace_url_patient_id(self, url, patient_id):
        return url.replace("{patient_id}", patient_id)

    def validate_post_code(self, addresses):
        """There are two address_type
         1 - Primary Address
         2 - Secondary Address
        check post code matches"""

        valid = False
        print(addresses)
        for address in addresses:
            if str(self.post_code) == address["postcode"]:
                valid = True
                break
        return valid

    def get_patient_addresses(self, patient_id):
        try:
            responce_status, patient_addresses_responce = self.get_json_response(
                self.replace_url_patient_id(self.demographics, patient_id)
            )

            if responce_status != 200:
                frappe.throw("Error: Invalid API Request/Response")

            elif not self.validate_post_code(patient_addresses_responce):
                frappe.throw("Post Code does not match")

            return patient_addresses_responce[0]

        except Exception as e:
            print("Error: ", e)

    def get_file_extension(self, url):
        path = url.split("/")[-1]

        file_extension = path.split(".")[-1].lower()

        return file_extension

    def check_file_type(self, url):
        file_extension = self.get_file_extension(url)

        if "pdf" in file_extension:
            return "PDF"
        elif "jpg" or "jpeg" or "png" or "gif" or "bmp" in file_extension:
            return "Image"
        elif "rtf" in file_extension:
            return "RTF"

    def get_file_data(self, url):
        # Here Accept: will be */*
        data_response = requests.get(url)

        # ------------------------------------------- should handle the encoding (base64) according to Mark.xml
        # ------------------------------------------- The correspondence output has base64 encoding format
        # ------------------------------------------- for reference use : https://base64.guru/converter/decode/file

        return str(data_response.content)

    def process_inner_urls(self, _response):
        for response in _response["data"]:
            # The attachment type and attachment contents are append in each response contents
            if response["attachmentUrl"] != None:
                response["documentType"] = self.check_file_type(
                    response["attachmentUrl"]
                )
                response["attachmentContent"] = self.get_file_data(
                    response["attachmentUrl"]
                )
        return _response

    def get_patient_correspondenceIn(self, patient_id):
        try:
            responce_status, patient_correspondenceIn_response = self.get_json_response(
                self.replace_url_patient_id(self.correspondence_in, patient_id)
            )

            if responce_status != 200:
                frappe.throw("Error: Invalid API Request/Response")

            patient_correspondenceIn_response = self.process_inner_urls(
                patient_correspondenceIn_response
            )

            return patient_correspondenceIn_response['data']

        except Exception as e:
            print("Error: ", e)

    def get_patient_correspondenceOut(self, patient_id):
        try:
            (
                responce_status,
                patient_correspondenceOut_response,
            ) = self.get_json_response(
                self.replace_url_patient_id(self.correspondence_out, patient_id)
            )

            if responce_status != 200:
                frappe.throw("Error: Invalid API Request/Response")

            patient_correspondenceOut_response = self.process_inner_urls(
                patient_correspondenceOut_response
            )

            return patient_correspondenceOut_response['data']

        except Exception as e:
            print("Error: ", e)

    def process_json(self):
        try:
            response_status, patient_search_response = self.get_json_response(
                self.search_endpoint
                + "?q="
                + self.encode("firstName", self.first_name)
                + self._and("lastName", self.last_name)
                + self._and("dob", self.date_of_birth)
            )

            if response_status != 200:
                frappe.throw("Error: Invalid API Request/Response")

            elif len(patient_search_response["data"]) == 0:
                frappe.throw("No Record Found!")

            else:
                self.patient_id = patient_search_response["data"][0]["id"]

                if self.patient_id:
                    self.details_dict["patientDetails"] = patient_search_response["data"][0]
                    self.details_dict["patientAddress"] = self.get_patient_addresses(
                        self.patient_id
                    )
                    if self.details_dict["patientAddress"] is not None:
                        self.details_dict[
                            "correspondenceInbound"
                        ] = self.get_patient_correspondenceIn(self.patient_id)
                        self.details_dict[
                            "correspondenceOutbound"
                        ] = self.get_patient_correspondenceOut(self.patient_id)
                    # print("details_dictionary is ready")

                

                with open(
                    f"/home/frappe/frappe-bench/sites/json/{self.patient_id}.json", "w"
                ) as outfile:
                    json.dump(self.details_dict, outfile)

        except Exception as e:
            print("Error:", e)

    def clear_credientials(self):
        self.authentication_key = "****"

    def save_xml_doc(self):
        with open(f"/home/frappe/frappe-bench/sites/xml/{self.patient_id}.xml", "rb") as file:
            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": self.patient_id + ".xml",
                    "folder": "Home/BPS",
                    "content": file.read(),
                }
            )
            file_doc.save()

    def clear_files(self):
        os.remove(f"/home/frappe/frappe-bench/sites/json/{self.patient_id}.json")
        os.remove(f"/home/frappe/frappe-bench/sites/xml/{self.patient_id}.xml")

    def validate(self):
        # checking only the post code!
        if not self.post_code.isdigit():
            frappe.throw("Invalid Post Code!")

        else:
            self.process_json()
            self.send_post_request(
                f"http://localhost:8080/ehr/api/v1/launch?patient_file={self.patient_id}.json&output_file={self.patient_id}.xml"
            )
            self.save_xml_doc()
            self.clear_files() #For Testing
            self.clear_credientials()
