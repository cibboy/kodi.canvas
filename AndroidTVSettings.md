Android TV–style multi‑level settings navigator in Kodi (Sections → Categories → Settings → Options)
You want the Android TV “drill‑in from left to right” pattern, with the active level always on the left, its sublevel on the right, and smooth “promotion” of the right pane to the left when you select. Kodi gives us three native levels (sections, categories, settings) and, for select/enumeration settings, a fourth “options” level. Below is a concrete, ready‑to‑implement design that replicates this behavior using JSON‑RPC for data and skin XML for the UX.

Target interaction model
Depth 1: Left shows sections, right shows categories for the focused section.
Depth 2: Left shows categories (of selected section), right shows settings (of focused category).
Depth 3: Left shows settings (of selected category), right shows options when the focused setting is an enum/select; booleans toggle inline; other types open editors in place.
Depth 4 (options): Left shows options for the selected setting as a radio list; selecting an option writes the setting and automatically pops back to Depth 3.
Navigation feels like Android TV:

D‑pad friendly, row‑centric lists with title + description and right‑aligned value/switch.
Selecting an item “promotes” the right pane to the left with a slide animation; the next sublevel appears on the right.
Back pops one depth, with reverse animation.
High‑level architecture
script.atvsettings (Python addon):

Reads and writes settings via JSON‑RPC: JSONRPC.Version, Settings.GetSections, Settings.GetCategories, Settings.GetSettings, Settings.SetSettingValue, Settings.GetSettingValue.
Maintains a small navigation state machine (depth stack).
Publishes presentation‑ready data via Window Properties and ListItem properties.
Exposes actions to load, enter, edit, back, and refresh sublevels.
CustomSettingsATV.xml (skin window):

Contains duplicated list controls for each level, positioned in left and right slots.
Uses visible conditions and slide/fade animations tied to the current depth and navigation direction.
Wires D‑pad events (onright/onclick/onback) to RunScript calls that advance or pop the state.
Depth mapping and transitions
Depth	Left pane shows	Right pane shows	Primary action
1	Sections	Categories of focused section	Click section → Depth 2
2	Categories	Settings of focused category	Click category → Depth 3
3	Settings	Options for focused select setting (if applicable)	Click enum → Depth 4; click boolean → toggle; others → editor
4	Options (radio list)	—	Select value → write → pop to 3
We model “push” and “pop” to control animation direction.

Python addon: stateful dispatcher
Create script.atvsettings and add the following entrypoint and modules. This version focuses on the depth machine and sublevel population.

# default.py
import sys, json, urllib.parse as urlparse
import xbmc, xbmcgui
from resources.lib import rpc, model, editors

WIN = xbmcgui.Window(13000)  # Home window as property bus

def prop(k, v=None):
    if v is None:
        return WIN.getProperty(k)
    WIN.setProperty(k, v)

def clear_prefix(prefix, maxn=1000):
    for i in range(maxn):
        for key in ("Id","Label","Help","Type","Display","Raw","Constraints","Enabled","Selected"):
            WIN.clearProperty(f"{prefix}.{i}.{key}")

def set_depth(d, direction="push"):
    prop("ATV.Depth", str(d))
    prop("ATV.NavDirection", direction)  # push | pop

def load_sections():
    secs = rpc.get_sections()
    clear_prefix("ATV.Sections")
    prop("ATV.Sections.Count", str(len(secs)))
    for i, s in enumerate(secs):
        WIN.setProperty(f"ATV.Sections.{i}.Id", s.get("id",""))
        WIN.setProperty(f"ATV.Sections.{i}.Label", s.get("label",""))

def load_categories(section_id):
    cats = rpc.get_categories(section_id)
    clear_prefix("ATV.Categories")
    prop("ATV.Categories.Count", str(len(cats)))
    for i, c in enumerate(cats):
        WIN.setProperty(f"ATV.Categories.{i}.Id", c.get("id",""))
        WIN.setProperty(f"ATV.Categories.{i}.Label", c.get("label",""))

def load_settings(section_id, category_id, level):
    items = rpc.get_settings(section_id, category_id, level)
    clear_prefix("ATV.Settings")
    prop("ATV.Settings.Count", str(len(items)))
    for i, s in enumerate(items):
        row = model.normalize_setting(s)
        WIN.setProperty(f"ATV.Settings.{i}.Id", row["id"])
        WIN.setProperty(f"ATV.Settings.{i}.Label", row["label"])
        WIN.setProperty(f"ATV.Settings.{i}.Help", row["help"])
        WIN.setProperty(f"ATV.Settings.{i}.Type", row["type"])
        WIN.setProperty(f"ATV.Settings.{i}.Display", row["display"])
        WIN.setProperty(f"ATV.Settings.{i}.Raw", row["raw"])
        WIN.setProperty(f"ATV.Settings.{i}.Constraints", row["constraints"])
        WIN.setProperty(f"ATV.Settings.{i}.Enabled", row["enabled"])

def load_options(setting_index):
    # Read options for the focused setting from stored constraints
    cons = WIN.getProperty(f"ATV.Settings.{setting_index}.Constraints")
    rawv = WIN.getProperty(f"ATV.Settings.{setting_index}.Raw")
    sid = WIN.getProperty(f"ATV.Settings.{setting_index}.Id")
    label = WIN.getProperty(f"ATV.Settings.{setting_index}.Label")
    prop("ATV.Options.ForSettingId", sid or "")
    prop("ATV.Options.ForSettingLabel", label or "")

    clear_prefix("ATV.Options")
    options = model.options_from_constraints(cons)
    current = json.loads(rawv) if rawv else None
    prop("ATV.Options.Count", str(len(options)))
    for i, (opt_label, opt_value) in enumerate(options):
        WIN.setProperty(f"ATV.Options.{i}.Label", opt_label)
        WIN.setProperty(f"ATV.Options.{i}.Value", json.dumps(opt_value))
        WIN.setProperty(f"ATV.Options.{i}.Selected", "true" if opt_value == current else "false")

def push(args):
    depth = int(prop("ATV.Depth") or "1")
    section = args.get("section") or prop("ATV.Active.Section")
    category = args.get("category") or prop("ATV.Active.Category")
    level = args.get("level") or (prop("ATV.Level") or "standard")
    idx = int(args.get("index", "-1"))

    if depth == 1:
        # Selecting a section
        if args.get("section"):
            prop("ATV.Active.Section", args["section"])
        load_categories(prop("ATV.Active.Section"))
        set_depth(2, "push")

    elif depth == 2:
        # Selecting a category
        if args.get("category"):
            prop("ATV.Active.Category", args["category"])
        load_settings(prop("ATV.Active.Section"), prop("ATV.Active.Category"), level)
        set_depth(3, "push")

    elif depth == 3:
        # Selecting a setting
        s_type = WIN.getProperty(f"ATV.Settings.{idx}.Type")
        sid = WIN.getProperty(f"ATV.Settings.{idx}.Id")
        cons = WIN.getProperty(f"ATV.Settings.{idx}.Constraints")
        raw = WIN.getProperty(f"ATV.Settings.{idx}.Raw")

        if s_type == "boolean":
            newv = editors.edit_boolean(sid, json.loads(raw))
            if newv is not None:
                fresh = rpc.get_value(sid)
                disp = model.stringify("boolean", fresh, json.loads(cons or "{}"))
                WIN.setProperty(f"ATV.Settings.{idx}.Display", disp)
            return
        elif s_type == "select":
            load_options(idx)
            prop("ATV.Active.SettingIndex", str(idx))
            set_depth(4, "push")
        else:
            # Open inline editors
            if s_type in ("integer","number"):
                newv = editors.edit_number(sid, json.loads(raw), json.loads(cons or "{}"))
            elif s_type == "string":
                newv = editors.edit_string(sid, json.loads(raw))
            elif s_type == "path":
                newv = editors.edit_path(sid, json.loads(raw), folder=True)
            elif s_type == "color":
                newv = editors.edit_color(sid, json.loads(raw))
            else:
                newv = None
            if newv is not None:
                fresh = rpc.get_value(sid)
                disp = model.stringify(s_type, fresh, json.loads(cons or "{}"))
                WIN.setProperty(f"ATV.Settings.{idx}.Display", disp)

    elif depth == 4:
        # Selecting an option (radio)
        opt_val = args.get("opt_value")
        sid = prop("ATV.Options.ForSettingId")
        if sid and opt_val is not None:
            rpc.set_value(sid, json.loads(opt_val))
            # Refresh display in settings list
            sidx = int(prop("ATV.Active.SettingIndex") or "-1")
            cons = WIN.getProperty(f"ATV.Settings.{sidx}.Constraints")
            fresh = rpc.get_value(sid)
            disp = model.stringify("select", fresh, json.loads(cons or "{}"))
            WIN.setProperty(f"ATV.Settings.{sidx}.Raw", json.dumps(fresh))
            WIN.setProperty(f"ATV.Settings.{sidx}.Display", disp)
        # Pop back to settings
        set_depth(3, "pop")

def pop(_args=None):
    depth = int(prop("ATV.Depth") or "1")
    if depth <= 1:
        xbmc.executebuiltin("Action(Back)")
        return
    set_depth(depth - 1, "pop")

def sync_right_on_focus(args):
    # Called when left focus changes to update the right pane without pushing
    depth = int(prop("ATV.Depth") or "1")
    if depth == 1 and args.get("section"):
        prop("ATV.Active.Section", args["section"])
        load_categories(args["section"])
    elif depth == 2 and args.get("category"):
        prop("ATV.Active.Category", args["category"])
        level = prop("ATV.Level") or "standard"
        load_settings(prop("ATV.Active.Section"), args["category"], level)
    elif depth == 3:
        # Right pane is options only when focused is select; we update options preview on demand
        pass

def init(_args=None):
    prop("ATV.Level", "standard")
    load_sections()
    # Prime categories for the first section if desired (optional)
    set_depth(1, "push")

def run():
    args = {}
    if len(sys.argv) > 1 and sys.argv[1].startswith("?"):
        args = dict(urlparse.parse_qsl(sys.argv[1][1:]))
    action = args.get("action", "")
    if action == "init": return init(args)
    if action == "push": return push(args)
    if action == "pop": return pop(args)
    if action == "sync": return sync_right_on_focus(args)

if __name__ == "__main__":
    run()
Support modules:

# resources/lib/rpc.py
import json, xbmc
def call(method, params=None, _id=1):
    payload = {"jsonrpc":"2.0","method":method,"id":_id}
    if params is not None: payload["params"]=params
    return json.loads(xbmc.executeJSONRPC(json.dumps(payload)))
def get_sections():
    return call("Settings.GetSections", {"properties":["label"]}).get("result",{}).get("sections",[])
def get_categories(section):
    return call("Settings.GetCategories", {"section":section,"properties":["label","level"]}).get("result",{}).get("categories",[])
def get_settings(section, category, level):
    params={"section":section,"category":category,"level":level,
            "properties":["label","help","type","value","default","level","constraints","enabled"]}
    return call("Settings.GetSettings", params).get("result",{}).get("settings",[])
def set_value(setting_id, value):
    return call("Settings.SetSettingValue", {"setting":setting_id,"value":value})
def get_value(setting_id):
    return call("Settings.GetSettingValue", {"setting":setting_id}).get("result",{}).get("value")
# resources/lib/model.py
import json, xbmc
ON = xbmc.getLocalizedString(24020); OFF = xbmc.getLocalizedString(24021)
def stringify(typ, value, constraints):
    if typ=="boolean": return ON if bool(value) else OFF
    if typ in ("integer","number"): return str(value)
    if typ=="select":
        opts = (constraints or {}).get("options") or []
        if opts and isinstance(opts[0], dict):
            for o in opts:
                if o.get("value")==value: return o.get("label") or str(value)
        else:
            try: return str(opts[int(value)])
            except Exception: return str(value)
    if typ=="color":
        if isinstance(value,int): return "#{:08X}".format(value)
    return "" if value is None else str(value)
def normalize_setting(s):
    t = s.get("type","string")
    cons = s.get("constraints") or {}
    val = s.get("value")
    return {
        "id": s.get("id",""),
        "label": s.get("label",""),
        "help": s.get("help",""),
        "type": t,
        "display": stringify(t, val, cons),
        "raw": json.dumps(val),
        "constraints": json.dumps(cons),
        "enabled": "true" if s.get("enabled", True) else "false",
    }
def options_from_constraints(cons_json):
    cons = json.loads(cons_json) if cons_json else {}
    opts = cons.get("options") or []
    if opts and isinstance(opts[0], dict):
        return [(o.get("label",""), o.get("value")) for o in opts]
    return [(str(lbl), i) for i, lbl in enumerate(opts)]
# resources/lib/editors.py
import json, xbmcgui
from . import rpc
def edit_boolean(setting_id, current):
    newv = not bool(current); rpc.set_value(setting_id, newv); return newv
def edit_number(setting_id, current, constraints):
    rng = (constraints or {}).get("range") or {}; dlg=xbmcgui.Dialog()
    s = dlg.numeric(0, "Set value", str(current)); 
    if not s: return None
    try: num = int(s) if isinstance(current,int) else float(s)
    except ValueError: return None
    mn, mx = rng.get("minimum"), rng.get("maximum")
    if mn is not None: num = max(num, mn)
    if mx is not None: num = min(num, mx)
    rpc.set_value(setting_id, num); return num
def edit_string(setting_id, current):
    dlg=xbmcgui.Dialog(); s=dlg.input("Enter value", defaultt=str(current or ""))
    if s is None: return None
    rpc.set_value(setting_id, s); return s
def edit_path(setting_id, current, folder=True):
    dlg=xbmcgui.Dialog()
    p = dlg.browse(0 if folder else 1, "Choose", "files", "", False, False, str(current or ""))
    if not p: return None
    rpc.set_value(setting_id, p); return p
def edit_color(setting_id, current):
    dlg=xbmcgui.Dialog(); s=dlg.input("Enter color (ARGB hex)", defaultt=str(current or "#FFFFFFFF"))
    if not s: return None
    rpc.set_value(setting_id, s); return s
Skin window: multi‑pane layout with animated promotion
We place two slots (Left, Right). Each level (Sections, Categories, Settings, Options) exists twice: one anchored in the left slot and one in the right slot. Visible conditions switch which lists render in which slot based on ATV.Depth. Animations slide in the correct direction for push/pop.

<!-- 1080i/CustomSettingsATV.xml -->
<window id="12120">
  <defaultcontrol always="true">L.Sections</defaultcontrol>
  <onload>RunScript(script.atvsettings,action=init)</onload>
  <onback>RunScript(script.atvsettings,action=pop)</onback>

  <controls>

    <!-- Left slot (x=72), Right slot (x=720) -->
    <!-- LEFT: Sections at Depth 1 -->
    <list id="L.Sections">
      <posx>72</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),1)</visible>
      <animation effect="slide" start="0,0" end="0,0" time="0" reversible="false" condition="true">Conditional</animation>
      <itemlayout height="84">
        <control type="label"><label>$INFO[ListItem.Label]</label><font>font28</font></control>
      </itemlayout>
      <focusedlayout height="84">
        <control type="label"><label>$INFO[ListItem.Label]</label><font>font28_bold</font></control>
      </focusedlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Sections.0.Label)]</label>
          <property name="id">$INFO[Window.Property(ATV.Sections.0.Id)]</property>
        </item>
        <!-- Repeat with includes up to ATV.Sections.Count -->
      </content>
      <!-- Keep right pane synced as focus changes -->
      <onright>RunScript(script.atvsettings,action=push,section=$INFO[ListItem.Property(id)])</onright>
      <onfocus>RunScript(script.atvsettings,action=sync,section=$INFO[ListItem.Property(id)])</onfocus>
      <onclick>RunScript(script.atvsettings,action=push,section=$INFO[ListItem.Property(id)])</onclick>
    </list>

    <!-- RIGHT: Categories preview at Depth 1 -->
    <list id="R.Categories">
      <posx>720</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),1)</visible>
      <animation effect="slide" time="200" start="100,0" end="0,0" tween="quadratic">VisibleChange</animation>
      <itemlayout height="84">
        <control type="label"><label>$INFO[ListItem.Label]</label><font>font28</font></control>
      </itemlayout>
      <focusedlayout height="84">
        <control type="label"><label>$INFO[ListItem.Label]</label><font>font28_bold</font></control>
      </focusedlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Categories.0.Label)]</label>
          <property name="id">$INFO[Window.Property(ATV.Categories.0.Id)]</property>
        </item>
        <!-- Repeat -->
      </content>
    </list>

    <!-- LEFT: Categories at Depth 2 -->
    <list id="L.Categories">
      <posx>72</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),2)</visible>
      <animation effect="slide" time="240" start="648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),push)">Conditional</animation>
      <animation effect="slide" time="240" start="-648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),pop)">Conditional</animation>
      <itemlayout height="84"><control type="label"><label>$INFO[ListItem.Label]</label></control></itemlayout>
      <focusedlayout height="84"><control type="label"><label>$INFO[ListItem.Label]</label><font>font28_bold</font></control></focusedlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Categories.0.Label)]</label>
          <property name="id">$INFO[Window.Property(ATV.Categories.0.Id)]</property>
        </item>
      </content>
      <onfocus>RunScript(script.atvsettings,action=sync,category=$INFO[ListItem.Property(id)])</onfocus>
      <onright>RunScript(script.atvsettings,action=push,category=$INFO[ListItem.Property(id)],level=$INFO[Window.Property(ATV.Level)])</onright>
      <onclick>RunScript(script.atvsettings,action=push,category=$INFO[ListItem.Property(id)],level=$INFO[Window.Property(ATV.Level)])</onclick>
    </list>

    <!-- RIGHT: Settings preview at Depth 2 -->
    <list id="R.Settings@2">
      <posx>720</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),2)</visible>
      <animation effect="slide" time="200" start="100,0" end="0,0">VisibleChange</animation>
      <itemlayout height="110">
        <control type="label"><posx="0" /><posy>0</posy><label>$INFO[ListItem.Label]</label><font>font28</font></control>
        <control type="label"><posx="0" /><posy>40</posy><label>$INFO[ListItem.Property(help)]</label><font>font22</font><textcolor>secondary_text</textcolor></control>
        <control type="label"><posx="0" /><posy>0</posy><width>600</width><align>right</align><label>$INFO[ListItem.Property(display)]</label></control>
      </itemlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Settings.0.Label)]</label>
          <property name="help">$INFO[Window.Property(ATV.Settings.0.Help)]</property>
          <property name="display">$INFO[Window.Property(ATV.Settings.0.Display)]</property>
        </item>
      </content>
    </list>

    <!-- LEFT: Settings at Depth 3 -->
    <list id="L.Settings">
      <posx>72</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),3)</visible>
      <animation effect="slide" time="240" start="648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),push)">Conditional</animation>
      <animation effect="slide" time="240" start="-648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),pop)">Conditional</animation>
      <itemlayout height="110">
        <control type="label"><posx>0</posx><posy>0</posy><label>$INFO[ListItem.Label]</label><font>font28</font></control>
        <control type="label"><posx>0</posx><posy>40</posy><label>$INFO[ListItem.Property(help)]</label><font>font22</font><textcolor>secondary_text</textcolor></control>
        <control type="label"><posx>0</posx><posy>0</posy><width>600</width><align>right</align><label>$INFO[ListItem.Property(display)]</label>
          <visible>!String.IsEqual(ListItem.Property(type),boolean)</visible>
        </control>
      </itemlayout>
      <focusedlayout height="140">...</focusedlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Settings.0.Label)]</label>
          <property name="id">$INFO[Window.Property(ATV.Settings.0.Id)]</property>
          <property name="help">$INFO[Window.Property(ATV.Settings.0.Help)]</property>
          <property name="type">$INFO[Window.Property(ATV.Settings.0.Type)]</property>
          <property name="display">$INFO[Window.Property(ATV.Settings.0.Display)]</property>
          <property name="raw">$INFO[Window.Property(ATV.Settings.0.Raw)]</property>
          <property name="constraints">$INFO[Window.Property(ATV.Settings.0.Constraints)]</property>
          <property name="index">0</property>
        </item>
        <!-- Repeat -->
      </content>
      <!-- Edit behaviors -->
      <onclick condition="String.IsEqual(ListItem.Property(type),boolean)">
        RunScript(script.atvsettings,action=push,index=$INFO[ListItem.Property(index)])
      </onclick>
      <onclick condition="String.IsEqual(ListItem.Property(type),select)">
        RunScript(script.atvsettings,action=push,index=$INFO[ListItem.Property(index)])
      </onclick>
      <onclick condition="!String.IsEqual(ListItem.Property(type),boolean) + !String.IsEqual(ListItem.Property(type),select)">
        RunScript(script.atvsettings,action=push,index=$INFO[ListItem.Property(index)])
      </onclick>
      <onright condition="String.IsEqual(ListItem.Property(type),select)">
        RunScript(script.atvsettings,action=push,index=$INFO[ListItem.Property(index)])
      </onright>
    </list>

    <!-- RIGHT: Options (radio) at Depth 4 -->
    <list id="R.Options">
      <posx>720</posx><posy>120</posy><width>600</width><height>840</height>
      <visible>String.IsEqual(Window.Property(ATV.Depth),4)</visible>
      <animation effect="slide" time="240" start="648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),push)">Conditional</animation>
      <animation effect="slide" time="240" start="-648,0" end="0,0" condition="String.IsEqual(Window.Property(ATV.NavDirection),pop)">Conditional</animation>
      <itemlayout height="84">
        <control type="image"><posx>0</posx><posy>26</posy><width>32</width><height>32</height>
          <texture>radio_off.png</texture>
          <visible>String.IsEmpty(ListItem.Property(selected))</visible>
        </control>
        <control type="image"><posx>0</posx><posy>26</posy><width>32</width><height>32</height>
          <texture>radio_on.png</texture>
          <visible>String.IsEqual(ListItem.Property(selected),true)</visible>
        </control>
        <control type="label"><posx>48</posx><posy>18</posy><label>$INFO[ListItem.Label]</label></control>
      </itemlayout>
      <focusedlayout height="84">...</focusedlayout>
      <content>
        <item id="0">
          <label>$INFO[Window.Property(ATV.Options.0.Label)]</label>
          <property name="opt_value">$INFO[Window.Property(ATV.Options.0.Value)]</property>
          <property name="selected">$INFO[Window.Property(ATV.Options.0.Selected)]</property>
        </item>
        <!-- Repeat -->
      </content>
      <onclick>RunScript(script.atvsettings,action=push,opt_value=$INFO[ListItem.Property(opt_value)])</onclick>
    </list>

  </controls>
</window>
Notes:

Each list’s <content> block should be generated up to the corresponding Count property via includes/macros for real usage.
Visible and animation conditions hinge on Window.Properties ATV.Depth and ATV.NavDirection, set by the script on push/pop.
Remote‑friendly row design (Android TV feel)
Row title + secondary description in the same item; right‑aligned value or a switch glyph for booleans.
Strong focus styling: scale up + background glow in focusedlayout.
Radio options show selected state with large radio icons and generous row height.
Keep left pane dense, right pane immersive.
Event wiring and focus behavior
Left pane controls the right pane content. As the user scrolls left at any depth, onfocus triggers a lightweight RunScript(action=sync, ...) to reload the right pane’s items without changing depth.
Pressing RIGHT moves focus to the right pane; pressing OK in the left pane also pushes to the next depth.
Back pops one depth and restores focus to the left pane at the correct row.
Editing behavior per type
boolean: Toggle in place at Depth 3; update display immediately.
select: Push to Depth 4; write on selection; pop back to Depth 3.
integer/number: Open numeric dialog; on success, update display; remain at Depth 3.
string/path/color: Open appropriate dialog; update and remain.
Breadcrumbs and level filter
Maintain Window.Property(ATV.Breadcrumbs) like “System › Audio › Advanced”. Update on push/pop/sync.
Maintain Window.Property(ATV.Level) for filtering Settings.GetSettings (basic/standard/advanced/expert). Provide a small button in the window to cycle level and refresh settings for the current category.
Performance and robustness
Cache sections and categories in memory (session‑scope) in the script; they rarely change.
Only re‑query settings on category change or level change; for edits, refresh a single item using Settings.GetSettingValue.
Normalize enum options that come as either a list of labels or a list of {label, value} objects.
Respect “enabled” and dependency flags from Settings.GetSettings; render disabled rows as non‑interactive.
Workarounds for skin engine constraints
No animation callbacks: Use property‑driven visible conditions and twin lists per level with slide/fade to simulate promotion. The script sets ATV.NavDirection=push/pop before flipping ATV.Depth to ensure correct direction.
Content duplication: Use <include> templates to generate <item> blocks up to Count, or switch to a WindowXMLDialog owned by the addon for ListItem injection if you prefer less property plumbing (you can still fully reskin it).
Option lists as pane instead of modal: This keeps the left‑right mental model; if you prefer a modal, reuse the earlier DialogATVRadio and skip Depth 4.
QA checklist
Open window → Depth=1; sections on left, categories on right for focused section.
Scroll sections → categories preview updates live.
Press OK/RIGHT on a section → left becomes categories, right becomes settings (slide left).
Scroll categories → settings preview updates live.
Press OK/RIGHT on a category → left becomes settings.
On a select setting: RIGHT/OK pushes to options on right; selecting a radio writes value and pops back.
On boolean: OK toggles and updates.
Back pops depth with reverse slide until close.
What I can tailor next
Generate the include macros for item replication in your skin.
Add focus animations and typography to match your brand.
Add “show changed only” and “reset category defaults”.
Implement an inline color picker control pane instead of hex input.
If you share your target Kodi version and current skin codebase, I’ll align JSON‑RPC normalization and skin control ids precisely and hand you a drop‑in addon + XML set.