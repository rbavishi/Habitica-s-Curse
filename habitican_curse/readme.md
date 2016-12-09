# General Architecture

# Data Flow
## Initialization
When HC is initiatied, a new instance of request manager is created which kicks off the first data pull. This does a pull of all user data and all task data (belonging to the user).  User data is populated into the status bar and tasks are added to the trinity display at the top.

Task are iterated over and a new MenuItem is created for each task, depending on its type.  Once all tasks have instantiated as a MenuItem, a new menu is created of each of the three types (habits, dailies, todos).  These menus are the only storage for tasks in the code (this might be bad?)
