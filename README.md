# xboard
Xboard is a CLI wrapper that connects to multiple XCC controllers at once and collects various info, i.e. voltage, leds, fans.
It uses python and ssh to make a connection and send commands to each controller in parallel.
The most important part is that it keeps an open shell so the connection can be interactive.
Other important features are: xboard keeps a log file where events and errors are thrown and a cfg file that keeps the configurations for further usages.
