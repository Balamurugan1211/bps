// Copyright (c) 2023, Techfinite Systems and contributors
// For license information, please see license.txt

frappe.ui.form.on('BPS', {
	refresh: function(frm) {
		  frm.add_custom_button(__('Browse'), function(){
			//frappe.msgprint(frm.doc.id)
			frappe.set_route('/app/file/view/home/BPS')
		});
	  }
});
