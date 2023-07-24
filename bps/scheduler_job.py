import frappe
from datetime import datetime, timedelta
from pytz import timezone


def delete_old_files():
    try:
        # Get the current time
        current_time = datetime.now(timezone('Asia/Kolkata'))

        # Calculate the time 5 minutes ago
        five_minutes_ago = current_time - timedelta(minutes=5)

        # Query for files older than 5 minutes excluding "Home" and "Attachments" folders
        old_files = frappe.get_list("File",
            filters={
                "creation": ("<", five_minutes_ago),
                 "folder": ["=","Home/BPS"]  # Exclude "Home" and "Attachments" folders
            },
            fields=["name"])

        # Delete the old files
        for file in old_files:
            frappe.delete_doc("File", file.name, ignore_permissions=True)
            frappe.db.commit()

        print(f"{len(old_files)} old files deleted successfully!")
    except Exception as e:
        print(f"Failed to delete old files: {str(e)}")

if __name__ == "__main__":
    delete_old_files()