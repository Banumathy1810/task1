import qutip as qt
from qutip.qip.circuit import QubitCircuit
from flask import Flask, request, send_file, render_template
import matplotlib
import logging
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)  # Suppress Matplotlib debug logs so that it wont show the warnings
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate_circuit', methods=['POST'])
def generate_circuit():
    data = request.json
    logging.debug(f"Received data: {data}")

    if not data:
        return {"error": "No data received"}, 400

    try:
        qubit_number = int(data["qubitNumber"])
        layers = data["layers"]

        logging.debug(f"Creating circuit with {qubit_number} qubits.")
        qc = QubitCircuit(qubit_number)

       #Layers and details for each gate
        for layer in layers:
            gate = layer["gate"].upper()

            if gate == "CNOT":
                if "controlQubit" not in layer or "targetQubit" not in layer:
                    return {"error": "CNOT gate requires controlQubit and targetQubit"}, 400

                try:
                    control = int(layer["controlQubit"])
                    target = int(layer["targetQubit"])
                except (ValueError, KeyError):
                    return {"error": "Invalid control or target qubit value for CNOT gate"}, 400

                if control == target:
                    return {"error": "Control and target qubit must be different for CNOT"}, 400
                if control >= qubit_number or target >= qubit_number:
                    return {"error": f"Qubit index out of range. Valid range: 0 to {qubit_number - 1}"}, 400

                logging.debug(f"Adding CNOT gate: control={control}, target={target}")
                qc.add_gate("CNOT", targets=[target], controls=[control])

            elif gate == "SWAP":
                if "qubit1" not in layer or "qubit2" not in layer:
                    return {"error": "SWAP gate requires qubit1 and qubit2"}, 400

                try:
                    qubit1 = int(layer["qubit1"])
                    qubit2 = int(layer["qubit2"])
                except (ValueError, KeyError):
                    return {"error": "Invalid qubit1 or qubit2 value for SWAP gate"}, 400

                if qubit1 >= qubit_number or qubit2 >= qubit_number:
                    return {"error": f"Qubit index out of range. Valid range: 0 to {qubit_number - 1}"}, 400

                logging.debug(f"Adding SWAP gate: qubit1={qubit1}, qubit2={qubit2}")
                qc.add_gate("SWAP", targets=[qubit1, qubit2])

            elif gate == "CZ":
                if "controlQubit" not in layer or "targetQubit" not in layer:
                    return {"error": "CZ gate requires controlQubit and targetQubit"}, 400

                try:
                    control = int(layer["controlQubit"])
                    target = int(layer["targetQubit"])
                except (ValueError, KeyError):
                    return {"error": "Invalid control or target qubit value for CZ gate"}, 400

                if control == target:
                    return {"error": "Control and target qubit must be different for CZ"}, 400
                if control >= qubit_number or target >= qubit_number:
                    return {"error": f"Qubit index out of range. Valid range: 0 to {qubit_number - 1}"}, 400

                logging.debug(f"Adding CZ gate: control={control}, target={target}")
                qc.add_gate("CZ", targets=[target], controls=[control])

            elif gate == "MEASURE":
                if "qubit" not in layer:
                    return {"error": "Measurement gate requires qubit"}, 400

                try:
                    qubit = int(layer["qubit"])
                except (ValueError, KeyError):
                    return {"error": "Invalid qubit value for Measurement gate"}, 400

                if qubit >= qubit_number:
                    return {"error": f"Qubit index out of range. Valid range: 0 to {qubit_number - 1}"}, 400

                logging.debug(f"Adding MEASURE gate: qubit={qubit}")
                qc.add_gate("MEASURE", targets=[qubit])

            else:
                if "qubit" not in layer:
                    return {"error": f"Gate {gate} requires qubit"}, 400

                try:
                    qubit = int(layer["qubit"])
                except (ValueError, KeyError):
                    return {"error": f"Invalid qubit value for {gate} gate"}, 400

                if qubit >= qubit_number:
                    return {"error": f"Qubit index out of range. Valid range: 0 to {qubit_number - 1}"}, 400

                logging.debug(f"Adding {gate} gate: qubit={qubit}")
                if gate == "H":
                    qc.add_gate("SNOT", targets=[qubit])  # SNOT is Hadamard in QuTiP
                elif gate in ["X", "Y", "Z", "T", "S"]:
                    qc.add_gate(gate, targets=[qubit])
                else:
                    return {"error": f"Invalid gate: {gate}"}, 400

        logging.debug("Circuit created successfully.")

        # Saving the circuit visualization here:
        os.makedirs("static", exist_ok=True)
        filename = "static/circuit.jpg"

        # To Draw the circuit and save it as an image we use qc.draw() method from QuTiP
        fig, ax = plt.subplots(figsize=(10, 4))
        qc.draw(ax=ax)
        plt.savefig(filename, format='jpg', bbox_inches='tight')
        plt.close()

        logging.debug(f"File saved: {filename}")

        # It should return the file:
        return send_file(filename, mimetype='image/jpeg')

    except Exception as e:
        logging.error(f"Error generating circuit: {e}")
        return {"error": f"An error occurred: {str(e)}"}, 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)