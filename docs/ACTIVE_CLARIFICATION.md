# Active Clarification

`ContextAnalyzer` extracts slots such as module model, order number, parameter name, interface name, alarm code, indicator state, network type, and expected output type.

If missing slots materially affect routing or evidence lookup, the Supervisor returns a clarification plan instead of calling all agents. The prompt asks for only the most important one or two fields and includes an industrial example.

After the user provides context, the same orchestrator reruns Context Analyzer and Supervisor with the updated input.

