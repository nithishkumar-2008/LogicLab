# ⚡ LogicLab — Interactive Digital Logic Simulator

<p align="center">
  <strong>Learn Boolean Logic. Visualize Circuits. Understand Every Output.</strong>
  <br>
  A simple, interactive way to explore the world of Digital Electronics.
</p>

---

## 💡 What is LogicLab?

**LogicLab** is an interactive, web-based Digital Logic Simulator that helps students understand Boolean algebra and digital logic through real-time simulation.

Instead of studying Boolean expressions, truth tables, and logic circuits separately, LogicLab brings them together in one place.

Enter a Boolean expression, simulate it, and explore the result through a truth table, circuit diagram, input switches, and a simple explanation.

> 🎯 **Our Goal:** Make Digital Logic easier to learn, visualize, and understand.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧮 Boolean Expression Editor | Enter expressions and use operator buttons to build logic expressions. |
| ⚡ Logic Circuit Generator | Generate SVG circuit diagrams from Boolean expressions. |
| 📊 Truth Table Generator | Automatically generate truth tables for up to 4 variables. |
| 🎚️ Interactive Input Switches | Change input values and observe the corresponding output. |
| 🔦 Live Signal Visualization | View HIGH and LOW signal states in the circuit. |
| 🧠 Logic Explanations | Understand the variables, operators, and gate-by-gate logic. |
| 🛡️ Safe Expression Parser | Parse expressions without using Python's `eval()` or `exec()`. |
| ❌ Helpful Error Messages | Identify invalid expressions and syntax mistakes. |
| 📋 Copy & Export | Copy truth tables and export them as CSV files. |
| 📚 Example Expressions | Explore ready-made Boolean expressions. |
| 🎨 Neon Circuit Lab UI | A dark interface with neon accents and colour-coded gates. |
| ⌨️ Accessible Interface | Keyboard accessibility and reduced-motion support. |

---

## 🖥️ Explore LogicLab

LogicLab includes five main sections:

### 1. 🏠 Dashboard
Get started with the simulator and explore its main features.

### 2. 🔌 Circuit Simulator
Enter a Boolean expression and visualize the corresponding logic circuit.

### 3. 📊 Truth Table
View the possible input combinations and their corresponding outputs.

### 4. 📚 Examples
Try example expressions to understand how different logic operations work.

### 5. ℹ️ About
Learn about LogicLab, its purpose, and the technologies behind it.

---

## ⚙️ How Does It Work?

LogicLab follows a simple workflow:

**Step 1 — Enter an Expression**

For example:

```text
A AND B
```

**Step 2 — Click Simulate**

LogicLab parses the expression and evaluates its Boolean logic.

**Step 3 — Explore the Results**

The application displays:
- The generated logic circuit.
- The complete truth table.
- Input switches and the current output.
- A plain-language explanation.

**Step 4 — Change the Inputs**

Change A or B and observe how the circuit output and highlighted truth-table row update.

**Step 5 — Experiment**

Try different expressions and learn how logic gates work.

---

## 🧪 Example: AND Gate

Consider the expression:

```text
A AND B
```

The AND gate produces an output of `1` only when both inputs are `1`.

| Input A | Input B | Output |
|:---:|:---:|:---:|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

**Try it yourself:** Enter `A AND B` in LogicLab and compare the simulated results with this truth table.

---

## 🔤 Supported Logic Operators

LogicLab currently supports four Boolean operators.

| Operator | Example | Meaning |
|---|---|---|
| AND | `A AND B` | Output is 1 when both inputs are 1. |
| OR | `A OR B` | Output is 1 when at least one input is 1. |
| NOT | `NOT A` | Reverses the input value. |
| XOR | `A XOR B` | Output is 1 when the inputs are different. |

### Additional Expression Support

- **Parentheses:** `(A AND B) OR C`
- **Constants:** `0` and `1`
- **Alternative symbols:** `∧`, `∨`, `¬`, `!`, `~`, `&`, `⊕`, and `^`
- **Case-insensitive keywords:** `AND`, `and`, and `And`
- **Operator precedence:** NOT → AND → XOR → OR

Parentheses can be used to control the order of evaluation.

---

## 🛠️ Technology Stack

LogicLab is built using lightweight web technologies.

| Technology | Purpose |
|---|---|
| 🐍 Python 3 | Backend logic and expression processing |
| 🌶️ Flask | Web server and API endpoints |
| 🌐 HTML5 | Page structure |
| 🎨 CSS3 | Styling and responsive interface |
| ⚡ JavaScript | Interactive simulation and navigation |
| 📐 SVG | Logic circuit diagrams |
| 🧪 pytest | Automated testing |

**No external CDNs or external fonts are required.** Once the required Python packages are installed, the application can run locally without external web resources.

---

## 📂 Project Structure

```text
LogicLab/
│
├── app.py                  # Flask application and API routes
├── logic_engine.py         # Tokenizer, parser, evaluation and truth tables
├── circuit_builder.py      # Circuit generation and circuit evaluation
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html          # Main web interface
│
├── static/
│   ├── css/
│   │   └── style.css       # UI styling
│   └── js/
│       └── script.js      # Frontend interactions
│
└── tests/
    ├── test_truth_table.py # Truth-table tests
    └── ...                 # Other test modules
```

*Note: The structure above reflects the documented architecture. Actual filenames may differ slightly depending on your project version.*

---

## 🚀 Getting Started

Follow these steps to run LogicLab on your computer.

### Prerequisites

- Python 3.9 or newer
- Visual Studio Code or another code editor
- A modern web browser

### Step 1: Open the Project

Open your LogicLab project folder in VS Code.

Open the integrated terminal:

**Terminal → New Terminal**

### Step 2: Create a Virtual Environment

```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, allow activation for the current terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

When activation succeeds, `(.venv)` appears at the beginning of your terminal prompt.

### Step 4: Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 5: Start the Application

```powershell
python app.py
```

Wait for Flask to display an address similar to:

```text
Running on http://127.0.0.1:5000
```

### Step 6: Open LogicLab

Open your browser and visit:

**http://127.0.0.1:5000**

🎉 That's it! LogicLab is ready to use.

**Important:** Keep the terminal open while using the application. Press `Ctrl + C` in the terminal to stop the server.

---

## 🧪 Run the Tests

LogicLab includes automated tests for checking its logic engine, truth tables, circuit generation, and API.

With your virtual environment activated, run:

```powershell
python -m pytest
```

The test results will help you identify whether the implemented functionality is working as expected.

---

## 🔗 API Overview

LogicLab exposes the following documented endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/simulate` | POST | Simulate an expression and retrieve results. |
| `/api/evaluate` | POST | Evaluate Boolean expressions. |
| `/api/examples` | GET | Retrieve example expressions. |

The server also checks that the circuit evaluator's output matches the expression evaluator's output in simulation responses.

---

## ⚠️ Current Limitations

LogicLab is designed primarily for learning basic Boolean logic.

- Supports a maximum of **4 distinct variables**.
- Variable names are single letters from A to Z.
- Maximum expression length is 200 characters.
- Supports AND, OR, NOT, and XOR operators.
- NAND, NOR, and XNOR are not currently supported.
- Complex multi-input operations are represented using chained two-input gates.
- Karnaugh maps and automatic Boolean expression minimization are not available yet.
- The Flask server must remain running while the application is being used.

---

## 🔮 Future Improvements

Potential features for future versions include:

- [ ] NAND, NOR, and XNOR gate support.
- [ ] Boolean expression simplification.
- [ ] Karnaugh map generation.
- [ ] Improved automatic wire routing.
- [ ] Circuit export as SVG or PNG.
- [ ] Shareable Boolean expressions through URLs.
- [ ] Support for more variables.
- [ ] Additional learning examples and guided exercises.

---

## 🎓 Who Is This Project For?

LogicLab is useful for:

- Electronics and Communication Engineering students.
- Electrical and Electronics Engineering students.
- Computer Science students learning Boolean algebra.
- Beginners studying Digital Electronics.
- Students practising truth tables and logic gates.

---

## 📸 Screenshots

Add screenshots of your actual application to a `screenshots/` folder.

Once the screenshots are added, display them here:

```markdown
![LogicLab Dashboard](screenshots/dashboard.png)
```

You can add more screenshots for the Circuit Simulator and Truth Table sections.

---

## 👨‍💻 About the Project

LogicLab is a learning-focused project built to make Boolean algebra and digital logic more interactive.

By combining expression evaluation, truth-table generation, and circuit visualization, it helps students connect theoretical concepts with their practical behaviour.

**Learn the logic. See the circuit. Understand the output.**

---

<p align="center">
  ⚡ <strong>LogicLab — Explore Digital Logic Visually.</strong>
</p>