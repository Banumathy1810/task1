import os
import logging
import qutip as qt
from qutip.qip.circuit import QubitCircuit
from flask import Flask, request, send_file, render_template
import matplotlib
import matplotlib.pyplot as plt


mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)
matplotlib.use('Agg')

#Setting up the flash app here,this is like this takes input from frontend and gives that to backent to process throught it to give a result,which is then given back to frontend 
app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/generate_circuit', methods=['POST'])
def generate_circuit():
    data = request.json
    logging.debug(f"[Request] Received data: {data}")

    if not data:
        return {"error": "No data received"}, 400

    try:
        qubit_number = int(data["qubitNumber"])
        layers = data["layers"]

        logging.info(f"Initializing quantum circuit with {qubit_number} qubits.")
        qc = QubitCircuit(qubit_number)

        for layer_idx, layer in enumerate(layers):
            gate = layer["gate"].upper()
            logging.debug(f"[Layer {layer_idx}] Processing gate: {gate}")

            if gate == "CNOT":
                control = int(layer["controlQubit"])
                target = int(layer["targetQubit"])

                if control == target:
                    return {"error": "Control and target qubits must differ for CNOT."}, 400

                qc.add_gate("CNOT", targets=[target], controls=[control])
                logging.info(f"Added CNOT gate (control={control}, target={target})")

            elif gate == "SWAP":
                qubit1 = int(layer["qubit1"])
                qubit2 = int(layer["qubit2"])

                qc.add_gate("SWAP", targets=[qubit1, qubit2])
                logging.info(f"Added SWAP gate between qubit {qubit1} and qubit {qubit2}")

            elif gate == "CZ":
                control = int(layer["controlQubit"])
                target = int(layer["targetQubit"])

                if control == target:
                    return {"error": "Control and target qubits must differ for CZ."}, 400

                qc.add_gate("CZ", targets=[target], controls=[control])
                logging.info(f"Added CZ gate (control={control}, target={target})")

            elif gate == "MEASURE":
                qubit = int(layer["qubit"])
                qc.add_gate("MEASURE", targets=[qubit])
                logging.info(f"Added MEASURE gate on qubit {qubit}")

            else:
                qubit = int(layer["qubit"])
                if gate == "H":
                    qc.add_gate("SNOT", targets=[qubit])
                    logging.info(f"Added Hadamard (SNOT) gate on qubit {qubit}")
                elif gate in ["X", "Y", "Z", "T", "S"]:
                    qc.add_gate(gate, targets=[qubit])
                    logging.info(f"Added {gate} gate on qubit {qubit}")
                else:
                    return {"error": f"Unsupported gate: {gate}"}, 400

        # This is bascially to store the output image
        os.makedirs("static", exist_ok=True)
        filename = "static/circuit.jpg"

        #CIRCUIT DRAWER
        logging.info("Rendering the quantum circuit diagram.")
        fig, ax = plt.subplots(figsize=(12, 4))
        qc.draw(ax=ax)
        plt.savefig(filename, format='jpg', bbox_inches='tight')
        plt.close()
        logging.info(f"Circuit diagram saved to '{filename}'")

        return send_file(filename, mimetype='image/jpeg')

    except Exception as e:
        logging.error(f"Unexpected error during circuit generation: {e}")
        return {"error": f"An error occurred: {str(e)}"}, 500


if __name__ == '__main__':
    # Here we can access the quantum circuit visualiser:click down
    logging.info("Quantum circuit service running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
