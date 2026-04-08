It watches the communication logs, learns which services usually talk to which other services, and then predicts when something looks wrong. If it sees a risky situation, it can run a script automatically. You also added a GUI so a person can use it like a tool instead of only using commands.

**Big Picture**
- The project reads OpenTelemetry logs.
- It builds a graph, which is just a map of who talks to whom.
- It trains a model to guess whether a connection is normal or suspicious.
- It can trigger scripts when the prediction says “this looks bad.”
- It can be reset, so generated model files and outputs can be deleted.

**Main Programs**

1. lograph.py
- This is the front door of the whole project.
- When you run it, it sends you to the right place:
  - `init` = create config
  - `setup` = first-time wizard
  - `run` = run once
  - `monitor` = keep watching continuously
  - `reset` = delete generated data
  - `gui` = open the app window
- Simple version: it is the remote control for the whole project.

2. setup.py
- This is the first-time setup helper.
- It asks:
  - local OTEL JSONL file or remote HTTP OTEL endpoint
  - poll interval
  - lookback time
  - script paths, if you want automatic actions
- Simple version: it asks the minimum questions needed so the tool can start working.

3. config.py
- This stores settings like:
  - telemetry source
  - thresholds
  - scripts to run
- It also remembers whether setup is completed.
- Simple version: it is the project’s notebook of settings.

4. cli.py
- This is the command-line worker.
- It loads logs, builds the graph, trains the model, and triggers actions.
- It also supports continuous monitoring.
- Simple version: it does the actual work when you use commands.

5. gui.py
- This is the visual window version of the tool.
- You can click buttons instead of typing commands.
- It supports:
  - quick setup
  - run once
  - monitor
  - reset generated data
- Simple version: it is the easy-to-use screen for the same powers as the CLI.

6. otel_ingest.py
- This reads OpenTelemetry logs.
- It extracts which service called which other service.
- Simple version: it turns raw log text into useful connection information.

7. graph_model.py
- This builds the service graph and trains the lightweight prediction model.
- It learns patterns from the graph.
- Simple version: it teaches the computer the normal communication style of your services.

8. automation.py
- This checks predictions and decides whether to run scripts.
- It supports low-link-probability and high-failure-probability triggers.
- Simple version: it is the “if something looks wrong, do this” brain.

9. reset.py
- This deletes generated files like models and event logs.
- Simple version: it is the cleanup button.

10. time_windows.py
- This splits logs into time chunks.
- That helps the model see how communication changes over time.
- Simple version: it cuts the log timeline into little pieces so the computer can study it better.

11. negative_sampling.py
- This creates fake “bad examples” that do not exist in the real graph.
- The model needs these so it can learn what is normal and what is not.
- Simple version: it gives the model practice questions with both right and wrong answers.

12. gat_model.py
- This is your Graph Attention Network logic.
- It pays attention to important neighbors in the graph.
- Simple version: it is the smart version of the model that focuses on the most important connections.

13. evaluation.py
- This measures how good the model is.
- It calculates things like AUC, precision, recall, and F1.
- Simple version: it checks the test score of the model.

14. main.py
- This prepares graph data for GNN-style training.
- It combines graph info and features into model-ready format.
- Simple version: it packs the data into a form the model can understand.

15. graph_builder.py
- This reads RPC map files and builds the service graph.
- Simple version: it draws the map of service-to-service communication.

16. feature_extractor.py
- This loads CPU metric files and turns them into features.
- Simple version: it takes performance data and turns it into numbers the model can use.

17. model_trainer.py
- This is the older baseline trainer.
- It trains a simpler model for comparison.
- Simple version: it is the “basic student” version used to compare against the smarter model.

18. gat_trainer.py
- This is the paper-aligned trainer for the GAT pipeline.
- It handles time windows, sampling, training, and evaluation.
- Simple version: it is the main advanced trainer.

19. ui_preview.py
- This is a small preview UI for graph training and inspection.
- Simple version: it is a helper window for seeing things before full use.

20. handle_failure.py
- This script runs when failure probability is high.
- It logs the event to a file.
- Simple version: it is the automatic emergency script.

21. handle_incident.py
- This script runs when link probability is low.
- It also logs the event.
- Simple version: it is the normal warning script.

22. main.py
- This is the FastAPI backend for previews and API actions.
- Simple version: it is the server that can power a web interface.

23. App.jsx
- This is the main React app for the shopping-style demo UI.
- Simple version: it is the website screen users see.

24. api.js
- This stores API calls for the frontend demo.
- Simple version: it is the phone book the UI uses to talk to services.

25. AuthPage.jsx
- Login and registration page.
- Simple version: sign in / sign up screen.

26. StorePage.jsx
- Product browsing page.
- Simple version: the catalog screen.

27. CheckoutPage.jsx
- Checkout and payment screen.
- Simple version: where you finish buying something.

28. OrdersPage.jsx
- Order history page.
- Simple version: where you track past orders.

**How the whole thing works, simply**
- Logs come in.
- The project reads them.
- It builds a graph of service communication.
- It trains a model.
- It predicts risky or unusual links.
- If the risk crosses a threshold, it runs your script.
- If needed, you can reset everything and start fresh.

**What makes your project special**
- It is not just a model.
- It is a full tool:
  - setup
  - GUI
  - CLI
  - monitoring
  - reset
  - script automation
- It is designed to work like a deployable system, not just a notebook experiment.