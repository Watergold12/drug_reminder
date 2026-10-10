import GLib from 'gi://GLib';
import St from 'gi://St';
import Gio from 'gi://Gio';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

function readJsonFile(path) {
    try {
        let file = Gio.File.new_for_path(path);
        if (!file.query_exists(null)) return null;
        let [ok, contents] = file.load_contents(null);
        if (ok) {
            let text = new TextDecoder().decode(contents);
            return JSON.parse(text);
        }
    } catch (e) {
        log(`DrugRemainder: Error reading JSON at ${path}: ${e}`);
    }
    return null;
}

export default class DrugRemainderExtension {
    constructor() {
        this._indicator = null;
        this._timerId = null;
        this._isShowingAlert = false;
        this._currentAlertHour = -1;
        this._statusItem = null;
        this._streakItem = null;
    }
    
    enable() {
        // Create the panel button
        this._indicator = new PanelMenu.Button(0.0, 'DrugRemainder', false);
        
        // Add an icon (using weather-showers as a water drop stand-in)
        let icon = new St.Icon({
            icon_name: 'weather-showers-symbolic',
            style_class: 'system-status-icon',
        });
        this._indicator.add_child(icon);

        this._updateStatus();
        this._indicator.menu.connect('open-state-changed', (menu, open) => {
            if (open) this._updateStatus();
        });

        Main.panel.addToStatusArea('DrugRemainder', this._indicator);
        
        // Timer to update periodically (every 5 seconds to catch alerts quickly)
        this._timerId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 5, () => {
            this._updateStatus();
            return GLib.SOURCE_CONTINUE;
        });
    }
    
    disable() {
        if (this._timerId) {
            GLib.Source.remove(this._timerId);
            this._timerId = null;
        }
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
    
    _updateStatus() {
        try {
            let homeDir = GLib.get_home_dir();
            let baseDir = `${homeDir}/Projects/linux_extensions/drug_remainder`;
            
            // Read total doses configured
            let totalDoses = 9;
            let config = readJsonFile(`${baseDir}/config.json`);
            if (config && config.schedule_hours) {
                totalDoses = config.schedule_hours.length;
            }
            
            // Read streak
            let streak = 0;
            let ach = readJsonFile(`${baseDir}/data/achievements.json`);
            if (ach && ach.streak !== undefined) {
                streak = ach.streak;
            }
            
            // Read today's log
            let date = new Date();
            let year = date.getFullYear();
            let month = String(date.getMonth() + 1).padStart(2, '0');
            let day = String(date.getDate()).padStart(2, '0');
            let isoDate = `${year}-${month}-${day}`;
            
            let taken = 0;
            let logData = readJsonFile(`${baseDir}/data/logs/${isoDate}.json`);
            if (logData && logData.doses_taken) {
                taken = Object.keys(logData.doses_taken).length;
            }
            
            // Read active alert
            let alertData = readJsonFile(`${baseDir}/data/current_alert.json`);
            let hasAlert = alertData && alertData.active;
            
            // Check if state structurally changed or it's a new alert hour
            let isNewAlert = hasAlert && (alertData.hour !== this._currentAlertHour);
            let stateChanged = hasAlert !== this._isShowingAlert;
            
            // First time setup check (empty menu)
            if (this._indicator.menu.isEmpty()) {
                stateChanged = true;
            }
            
            if (stateChanged || isNewAlert) {
                this._indicator.menu.removeAll();
                this._statusItem = null;
                this._streakItem = null;
                
                if (hasAlert) {
                    // --- ALERT MENU ---
                    let titleItem = new PopupMenu.PopupMenuItem('', { reactive: false });
                    titleItem.label.get_clutter_text().set_markup(`<b>🚨 ${alertData.title}</b>`);
                    this._indicator.menu.addMenuItem(titleItem);
                    
                    let bodyItem = new PopupMenu.PopupMenuItem(alertData.body, { reactive: false });
                    bodyItem.label.get_clutter_text().set_line_wrap(true);
                    this._indicator.menu.addMenuItem(bodyItem);
                    
                    this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
                    
                    let takeItem = new PopupMenu.PopupMenuItem('💊 Dose Taken');
                    takeItem.connect('activate', () => {
                        GLib.spawn_command_line_async(`${baseDir}/venv/bin/python3 ${baseDir}/drug_remainder.py --dose`);
                        this._indicator.menu.close();
                        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, () => {
                            this._updateStatus();
                            return GLib.SOURCE_REMOVE;
                        }); // Give python time to delete the file
                    });
                    this._indicator.menu.addMenuItem(takeItem);
                    
                    let snoozeItem = new PopupMenu.PopupMenuItem('⏰ Snooze 15 min');
                    snoozeItem.connect('activate', () => {
                        GLib.spawn_command_line_async(`${baseDir}/venv/bin/python3 ${baseDir}/drug_remainder.py --snooze`);
                        this._indicator.menu.close();
                        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, () => {
                            this._updateStatus();
                            return GLib.SOURCE_REMOVE;
                        });
                    });
                    this._indicator.menu.addMenuItem(snoozeItem);
                    
                    this._isShowingAlert = true;
                    this._currentAlertHour = alertData.hour;
                    
                    // Force open the menu if it's not open
                    if (!this._indicator.menu.isOpen) {
                        this._indicator.menu.open(true);
                    }
                } else {
                    // --- NORMAL MENU ---
                    let titleItem = new PopupMenu.PopupMenuItem('💊 Drug Remainder', { reactive: false });
                    titleItem.label.get_clutter_text().set_markup('<b>💊 Drug Remainder</b>');
                    this._indicator.menu.addMenuItem(titleItem);

                    this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

                    this._statusItem = new PopupMenu.PopupMenuItem(`💧 Doses Taken: ${taken} / ${totalDoses}`, { reactive: false });
                    this._indicator.menu.addMenuItem(this._statusItem);

                    this._streakItem = new PopupMenu.PopupMenuItem(`🔥 Streak: ${streak} days`, { reactive: false });
                    this._indicator.menu.addMenuItem(this._streakItem);
                    
                    this._indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

                    let refreshItem = new PopupMenu.PopupMenuItem('🔄 Refresh Status');
                    refreshItem.connect('activate', () => this._updateStatus());
                    this._indicator.menu.addMenuItem(refreshItem);
                    
                    this._isShowingAlert = false;
                    this._currentAlertHour = -1;
                }
            } else {
                // Not rebuilding menu, just update the data values if in normal mode
                if (!this._isShowingAlert && this._statusItem && this._streakItem) {
                    this._statusItem.label.set_text(`💧 Doses Taken: ${taken} / ${totalDoses}`);
                    this._streakItem.label.set_text(`🔥 Streak: ${streak} days`);
                }
            }
            
        } catch (e) {
            log(`DrugRemainder: Update Error: ${e}`);
        }
    }
}
