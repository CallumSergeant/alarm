This document provides the neccessary information to install an ALARM agent on a device on the network.

---

##  Generate an install command
### **URL:** `/dashboard/managed-devices/`

**Add New Device:**
Click blue "Add New Device" button, above the table of managed devices. By clicking this button, a new install token is generated in the database and is ready to be used to validate a new ALARM agent. **This token can only be used once.**

**Copy Generated Command:**
By either selecting the whole command and copying, or pressing the "Copy Command" grey button, copy the whole generated command and install token.

---

##  Run command on new machine

!!! warning "Important"
    Only Ubuntu 20.04 is supported.

#### **SSH into new machine:**
It is reccomended to SSH into the new machine using the same device that has the dashboard open, this ensures you can easily copy the isntall command to the new device.

#### **Ensure you have the correct permissions:**
This script requires `sudo` to run. See the documentation about the scripts to view exactly what they do and why they need this root permission. You can check if you have sudo permissions by running:

```
sudo -v
```

If this doesn't return an error, you will likely have the correct permissions to run the install script.

#### **Ensure the correct dependancies are installed:**
This script requires the following dependancies to be installed:

 - `sudo`
 - `curl`

Please ensure these are isntalled before trying to run the install script.

#### **Paste the copied install command:**
Paste the whole command into the terminal, and press Enter. This will ask for the password for the user to verify you have sudo access. Enter the correct password, press Enter. The install script will now run and show a log of what it is doing in the terminal.

!!! success 
    When it is completed it will display a message to inform the user and drop them back into the terminal.

#### **Return to the dashboard:**
When the install script has finished running it will mark the new device as registered on the ALARM dashboard. Upon returning to the dashboard you will see a green button marked "Complete Setup". Pressing this will take you back to the managed device list, where the new device will be present.

---

##  Important Notes

#### **Compatible Devices**
This version of ALARM has only be tested to successfully deploy an agent on an Ubuntu 20.04 machine. Other installs are not supported at this time.

---