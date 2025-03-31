This document provides the neccessary information to uninstall and remove an ALARM agent from a managed device on the network.

---

##  Generate the uninstall command
### **URL:** `/dashboard/managed-devices/`

**Remove device:**
By selecting the "Remove Device" action for the appropriate managed device, a popup will display the uninstall command.

**Copy Generated Command:**
By either selecting the whole command and copying, or pressing the "Copy Command" grey button, copy the whole generated command.

---

##  Run command on new machine

!!! warning "Important"
    Only run this script on machines that have the ALARM agent installed.

#### **SSH into new machine:**
It is reccomended to SSH into the new machine using the same device that has the dashboard open, this ensures you can easily copy the command to the new device.

#### **Paste the copied uninstall command:**
Paste the whole command into the terminal, and press Enter. The uninstall script will now run and show a log of what it is doing in the terminal.

!!! success 
    When it is completed it will display a message to inform the user and drop them back into the terminal.

#### **Return to the dashboard:**
When the uninstall script has finished running it will mark the new device as de-registered in the ALARM system and delete its entry in the database. Upon returning to the dashboard, refresh the managed device page, the uninstalled device will now be removed.