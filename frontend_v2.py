import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, ttk
from optical_properties import opt_prop, comp_split
from Batch_equation_splitting2 import eqtn_split
from Batch_calculation_gf3 import batch_calc
from mmsep_den_cn import M_M_sep, coord_num_avg
from pd_pf_opd import oxy_pack_density, effect_rem, optical_basicity
from density_v2 import molar_volume

cn_entries = []


def clear_fields():
    for entry in entries:
        entry.delete(0, tk.END)
    for cn_entry in cn_entries:
        cn_entry.delete(0, tk.END)
        cn_entry.insert(0, 0)
    text_output1.delete(1.0, tk.END)
    text_output2.delete(1.0, tk.END)
    text_output3.delete(1.0, tk.END)

def ask_rem_selection(elements):
    global selected_rem_elements
    selected_rem_elements = []

    def on_confirm():
        selected_rem_elements.clear()
        for var, element in zip(checkbox_vars, elements):
            if var.get():
                selected_rem_elements.append(element)
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title("Select Rare Earth Metals")
    dialog.geometry("400x200")

    checkbox_vars = []
    for element in elements:
        var = tk.BooleanVar()
        checkbox = tk.Checkbutton(dialog, text=element, variable=var, font=("Times New Roman", 14))
        checkbox.pack(anchor="w", padx=20, pady=5)
        checkbox_vars.append(var)

    confirm_button = tk.Button(dialog, text="Confirm", command=on_confirm, font=("Times New Roman", 14))
    confirm_button.pack(pady=10)

    dialog.grab_set()
    dialog.wait_window()


def calculate():
    global cations, batch_wt, weightfractions, density, compounds
    # Clear previous outputs before starting new calculations
    text_output1.delete(1.0, tk.END)
    text_output2.delete(1.0, tk.END)
    text_output3.delete(1.0, tk.END)

    try:
        eqn = entries[0].get()
        info = eqtn_split(eqn)
        moles, compounds, derived, oxides = info[0], info[1], info[2], info[3]
    except ValueError as ve:
        text_output1.insert(tk.END, f"ValueError: Please enter valid numeric values.\n{ve}")
    except Exception as e:
        text_output1.insert(tk.END, f"Error in equation splitting: {e}\n")
        return

    # Batch calculation
    try:
        batch_wt = float(entries[1].get())
        know = batch_calc(moles, compounds, derived, batch_wt)
        weightfractions, dermasses, total_compmass, grav_factors = know[0], know[1], know[2], know[3]
        org_mass = dermasses / 100
        text_output1.insert(tk.END,
                            f"Derived Mass: {round(total_compmass / 100, 4)}\nOriginal Mass: {round(org_mass, 4)}\n")
        text_output1.insert(tk.END,
                            f"\nWeight Fractions: \n")
        for i, wf in enumerate(weightfractions):
            text_output1.insert(tk.END,
                                f"{oxides[i]}:\t{wf}\n")
        text_output1.insert(tk.END,
                            f"\nGravimetric Factors: \n")
        for i, gf in enumerate(grav_factors):
            text_output1.insert(tk.END,
                                f"{oxides[i]}:\t{gf}\n")
    except ValueError as ve:
        text_output1.insert(tk.END, f"ValueError: Please enter valid numeric values.\n{ve}")
    except Exception as e:
        text_output1.insert(tk.END, f"Error in batch calculation: {e}\n")

    # Density calculation
    try:
        density = float(entries[2].get())
        Vm = molar_volume(org_mass, density)
        text_output1.insert(tk.END, f"\nMolar Volume: {Vm}\n")
        #text_output1.insert(tk.END, f"Density: {density}\n")

    except ValueError:
        try:
            density = simpledialog.askfloat("Density Input", f"Enter density of {im_liq}:", parent=root)
            Vm_info = molar_volume(wt_air, wt_liq, im_liq, org_mass)
            density, Vm = Vm_info[0], Vm_info[1]
            text_output1.insert(tk.END, f"\nMolar Volume: {Vm}\n")
            text_output1.insert(tk.END, f"\nDensity: {density}\n")
        except Exception as e:
            text_output1.insert(tk.END, f"Error in density calculation: {e}\n")

    # Metal-Metal separation
    try:
        sep_info = M_M_sep(moles, compounds, Vm)
        text_output2.insert(tk.END, "Metal-Metal Separation:\n")
        for oxd, m_m_sep in zip(oxides, sep_info[1]):
            text_output2.insert(tk.END, f"{oxd}: {m_m_sep:.4e}\n")
    except Exception as e:
        text_output2.insert(tk.END, f"Error in Metal-Metal separation: {e}\n")

    # Packing factor calculation
    try:
        lists = comp_split(info[3])
        cations, cat_occ, ox_occ = lists[0], lists[1], lists[2]

        opd_info = oxy_pack_density(cations, ox_occ, sep_info[0], Vm)
        text_output2.insert(tk.END, f"\nOxygen Packing Density: {opd_info[1]}\n")
    except Exception as e:
        text_output2.insert(tk.END, f"Error in packing factor calculation: {e}\n")
        return

    # Coordination number calculation
    try:
        if cn_entries:
            # Process each CN entry, if empty treat it as None
            cn_values = [float(cn_entry.get()) if cn_entry.get() else None for cn_entry in cn_entries]
        else:
            cn_values = None
        cn_info = coord_num_avg(sep_info[0], Vm, cn_values)
        text_output3.insert(tk.END, f"{cn_info}\n")
    except Exception as e:
        text_output3.insert(tk.END, f"Error in coordination number calculation: {e}\n")

    # Rare Earth Metal effect
    try:
        # Call effect_rem and retrieve results
        rem_infos = effect_rem(cations, batch_wt, weightfractions, density, compounds)
        z = rem_infos[0]  # Charge value (used internally, not displayed)
        rem_info = rem_infos[1]  # List of formatted results

        # Check the number of identified REMs
        if isinstance(rem_info, list) and rem_info:
            if len(rem_info) == 1:  # Single REM case
                text_output2.insert(tk.END, "\nRare Earth Metal Effect:\n")
                text_output2.insert(tk.END, rem_info[0])  # Directly display the single REM's results
            elif len(rem_info) > 1:  # Multiple REMs found
                # Extract REM names and trigger dialog
                rem_elements = [rem.split("\n")[0].split(":")[1].strip() for rem in rem_info]
                ask_rem_selection(rem_elements)

                if selected_rem_elements:
                    # Perform calculations for selected elements
                    rem_info = effect_rem(cations, batch_wt, weightfractions, density, compounds, selected_rem_elements)
                    text_output2.insert(tk.END, "\nSelected Rare Earth Metal Effects:\n")
                    for item in rem_info[1]:  # Access only the results part
                        text_output2.insert(tk.END, f"\n{item}\n")
                else:
                    text_output2.insert(tk.END, "No elements selected. No calculations performed.\n")
        else:
            text_output2.insert(tk.END, "No rare earth elements found.\n")
    except Exception as e:
        # Handle exceptions
        text_output2.insert(tk.END, f"Error in Rare Earth Metal effect calculation: {e}\n")

    # Optical Basicity calculation
    try:
        r_i = float(entries[3].get())
        ob_info = optical_basicity(cations, sep_info[0], Vm, r_i, opd_info[0], info[3])
        text_output3.insert(tk.END, f"{ob_info}\n")
    except Exception as e:
        text_output3.insert(tk.END, f"Error in optical basicity calculation: {e}\n")

    # Optical properties
    try:
        results = opt_prop(r_i, z, Vm)
        text_output3.insert(tk.END, f"\n{results}")
    except Exception as e:
        text_output3.insert(tk.END, f"Error in optical properties calculation: {e}\n")


def generate_cn_entries():
    response = messagebox.askyesno("Coordination Number Entry", "Do you want to enter coordination numbers?")
    if not response:
        return
    else:
        eqn = entries[0].get()
        info = eqtn_split(eqn)
        oxides = info[3]

        for widget in cn_frame.winfo_children():
            widget.destroy()

        global cn_entries
        cn_entries = []
        for i, oxide in enumerate(oxides):
            lbl = tk.Label(cn_frame, text=f"CN for {oxide}:", font=('Times New Roman', 14))
            lbl.grid(row=0, column=i * 2, padx=5, pady=5, sticky='e')

            entry = tk.Entry(cn_frame, width=5, font=('Times New Roman', 14))
            entry.grid(row=0, column=i * 2 + 1, padx=5, pady=5, sticky='w')

            cn_entries.append(entry)


def update_font_size(event=None):
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    base_size = max(12, int(min(window_width, window_height) / 50))

    label.config(font=("Times New Roman", base_size))
    for lbl, entry in zip(labels, entries):
        lbl.config(font=("Times New Roman", base_size))
        entry.config(font=("Times New Roman", base_size))

    button_generate_cn.config(font=("Times New Roman", base_size))
    button_calculate.config(font=("Times New Roman", base_size))
    button_clear.config(font=("Times New Roman", base_size))
    text_output1.config(font=("Times New Roman", base_size))
    text_output2.config(font=("Times New Roman", base_size))
    text_output3.config(font=("Times New Roman", base_size))


root = tk.Tk()
root.geometry("1900x1080")
root.title("PhysicalParameters_v1.2")

label = tk.Label(root, text="PhysicalParameters", font=('Times New Roman', 18))
label.pack()

labels_text = [
    "Equation:",
    "Batch Weight:",
    "Density",
    "Refractive index:",
]

labels = []
entries = []

for text in labels_text:
    frame = tk.Frame(root)
    frame.pack(padx=20, pady=10, fill=tk.X)

    lbl = tk.Label(frame, text=text, font=('Times New Roman', 14), width=20, anchor='w')
    lbl.pack(side=tk.LEFT, padx=(5, 10))

    entry = tk.Entry(frame, width=100, font=('Times New Roman', 14))
    entry.pack(side=tk.LEFT, padx=(0, 10))

    labels.append(lbl)
    entries.append(entry)

    if text == "Equation:":
        sample_frame = tk.Frame(root)
        sample_frame.pack(padx=0, pady=(0, 10), fill=tk.X)

        sample_label = tk.Label(sample_frame, text="Sample Equation : 20CaCO3[CaO] + 79.5NH4H2PO4[P2O5] + 0.5Dy2O3",
                                font=('Times New Roman', 16))
        sample_label.pack(anchor='w', padx=(25, 0))

button_generate_cn = tk.Button(root, text="Enter Coordination Numbers", width=50, command=generate_cn_entries)
button_generate_cn.pack(padx=20, pady=10)

cn_frame = tk.Frame(root)
cn_frame.pack(padx=20, pady=(0, 10))

button_frame = tk.Frame(root)
button_frame.pack(padx=20, pady=10)

button_calculate = tk.Button(button_frame, text="Calculate", width=25, command=calculate)
button_calculate.pack(side=tk.LEFT, padx=10)

button_clear = tk.Button(button_frame, text="Clear", width=25, command=clear_fields)
button_clear.pack(side=tk.LEFT, padx=10)

text_output1 = scrolledtext.ScrolledText(root, width=33, height=20, font=('Times New Roman', 16), padx=20, pady=20)
text_output1.pack(padx=10, pady=30, fill=tk.BOTH, expand=True, side=tk.LEFT)

text_output2 = scrolledtext.ScrolledText(root, width=33, height=20, font=('Times New Roman', 16), padx=20, pady=20)
text_output2.pack(padx=10, pady=30, fill=tk.BOTH, expand=True, side=tk.LEFT)

text_output3 = scrolledtext.ScrolledText(root, width=33, height=20, font=('Times New Roman', 16), padx=20, pady=20)
text_output3.pack(padx=10, pady=30, fill=tk.BOTH, expand=True, side=tk.LEFT)

root.bind('<Configure>', update_font_size)

root.mainloop()
