# -*- coding: utf-8 -*-
# Copyright (c) 2020, 4C Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import math
import frappe, json
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, date_diff, time_diff_in_hours, rounded
from erpnext.healthcare.doctype.inpatient_record.inpatient_record import set_details_from_ip_order
from erpnext.healthcare.utils import validate_customer_created, get_appointments_to_invoice, get_encounters_to_invoice, get_lab_tests_to_invoice, \
                                    get_clinical_procedures_to_invoice, get_therapy_sessions_to_invoice, get_inpatient_services_to_invoice

def validate_ipservices_dates(doc, method):
	for entry in doc.ip_services:
		if entry.start_date and entry.end_date and \
			get_datetime(entry.start_date) > get_datetime(entry.end_date):
			frappe.throw(_('Row #{0}: End datetime cannot be less than Start datetime').format(entry.idx))
    
@frappe.whitelist()
def schedule_discharge(args):
	discharge_order = json.loads(args)
	inpatient_record_id = frappe.db.get_value('Patient', discharge_order['patient'], 'inpatient_record')
	if inpatient_record_id:
		inpatient_record = frappe.get_doc('Inpatient Record', inpatient_record_id)
		check_out_inpatient(inpatient_record)
		set_details_from_ip_order(inpatient_record, discharge_order)
		inpatient_record.status = 'Discharge Scheduled'
		inpatient_record.save(ignore_permissions = True)
		frappe.db.set_value('Patient', discharge_order['patient'], 'inpatient_status', inpatient_record.status)
		frappe.db.set_value('Patient Encounter', inpatient_record.discharge_encounter, 'inpatient_status', inpatient_record.status)

def check_out_inpatient(inpatient_record):
	if inpatient_record.inpatient_occupancies:
		for inpatient_occupancy in inpatient_record.inpatient_occupancies:
			if inpatient_occupancy.left != 1:
				inpatient_occupancy.left = True
				inpatient_occupancy.check_out = now_datetime()
				frappe.db.set_value("Healthcare Service Unit", inpatient_occupancy.service_unit, "occupancy_status", "Vacant")

	if inpatient_record.ip_services:
		for ip_service in inpatient_record.ip_services:
			if ip_service.stopped != 1:
				ip_service.stopped = True
				if not ip_service.end_date:
					ip_service.end_date = now_datetime()

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
				days_used = date_diff(ip_service.end_date, ip_service.start_date) + 1
				qty = service_type.uom_per_day * days_used
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