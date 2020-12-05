# -*- coding: utf-8 -*-
# Copyright (c) 2020, 4C Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import math
import frappe, json
from frappe import _
from frappe.model.document import Document
from frappe.utils import (date_diff, time_diff_in_hours, rounded)
from erpnext.healthcare.utils import (validate_customer_created, get_appointments_to_invoice, get_encounters_to_invoice,
									get_lab_tests_to_invoice, get_clinical_procedures_to_invoice, get_therapy_sessions_to_invoice)

@frappe.whitelist()
def get_healthcare_services_to_invoice(patient, company):
    patient = frappe.get_doc('Patient', patient)
    items_to_invoice = []
    if patient:
        validate_customer_created(patient)
        # Customer validated, build a list of billable services
        items_to_invoice += get_appointments_to_invoice(patient, company)
        items_to_invoice += get_encounters_to_invoice(patient, company)
        items_to_invoice += get_lab_tests_to_invoice(patient, company)
        items_to_invoice += get_clinical_procedures_to_invoice(patient, company)
        items_to_invoice += get_inpatient_services_to_invoice(patient, company)
        items_to_invoice += get_therapy_sessions_to_invoice(patient, company)
        items_to_invoice += get_ip_services_to_invoice(patient, company)

        return items_to_invoice

def get_inpatient_services_to_invoice(patient, company):
	services_to_invoice = []
	inpatient_services = frappe.db.sql(
		'''
			SELECT
				io.*
			FROM
				`tabInpatient Record` ip, `tabInpatient Occupancy` io
			WHERE
				ip.patient=%s
				and ip.company=%s
				and io.parent=ip.name
				and io.left=1
				and io.invoiced=0
		''', (patient.name, company), as_dict=1)

	for inpatient_occupancy in inpatient_services:
		service_unit_type = frappe.db.get_value('Healthcare Service Unit', inpatient_occupancy.service_unit, 'service_unit_type')
		service_unit_type = frappe.get_cached_doc('Healthcare Service Unit Type', service_unit_type)
		if service_unit_type and service_unit_type.is_billable:
			hours_occupied = time_diff_in_hours(inpatient_occupancy.check_out, inpatient_occupancy.check_in)
			qty = 0.5
			if hours_occupied > 0:
				actual_qty = hours_occupied / service_unit_type.no_of_hours
				floor = math.floor(actual_qty)
				decimal_part = actual_qty - floor
				if decimal_part > 0.5:
					qty = rounded(floor + 1, 1)
				elif decimal_part < 0.5 and decimal_part > 0:
					qty = rounded(floor + 0.5, 1)
				if qty <= 0:
					qty = 0.5
			services_to_invoice.append({
				'reference_type': 'Inpatient Occupancy',
				'reference_name': inpatient_occupancy.name,
				'service': service_unit_type.item, 'qty': qty
			})

	return services_to_invoice

def get_ip_services_to_invoice(patient, company):
	services_to_invoice = []
	ip_services = frappe.db.sql(
			'''
			SELECT
				ips.*
			FROM
				`tabInpatient Record` ip, `tabIP Services` ips
			WHERE
				ip.patient=%s
				and ip.company=%s
				and ips.parent=ip.name
				and ips.stopped=1
				and ips.invoiced=0
		''', (patient.name, company), as_dict=1)

	for ip_service in ip_services:
		service_type = frappe.get_cached_doc('InPatient Service', ip_service.inpatient_service)
		if service_type and service_type.is_billable:
			if service_type.uom == 'Nos':
				if service_type.uom_per_day > 0:
					days_used = date_diff(ip_service.end_date, ip_service.start_date) + 1
					qty = service_type.uom_per_day * days_used
				else:
					qty = ip_service.qty
			else:
				hours_occupied = time_diff_in_hours(ip_service.end_date, ip_service.start_date)
				qty = 0.5
				if hours_occupied > 0:
					actual_qty = hours_occupied / service_type.no_of_hours
					floor = math.floor(actual_qty)
					decimal_part = actual_qty - floor
					if decimal_part > 0.5:
						qty = rounded(floor + 1, 1)
					elif decimal_part < 0.5 and decimal_part > 0:
						qty = rounded(floor + 0.5, 1)
					if qty <= 0:
						qty = 0.5

			services_to_invoice.append({
				'reference_type': 'IP Services',
				'reference_name': ip_service.name,
				'service': service_type.item, 'qty': qty
			})

	return services_to_invoice