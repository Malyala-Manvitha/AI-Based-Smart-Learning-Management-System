QUIZZES = {

    "Python": [

        {
            "question": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "define"],
            "answer": "def"
        },

        {
            "question": "Which symbol is used for comments in Python?",
            "options": ["//", "#", "/*", "--"],
            "answer": "#"
        },

        {
            "question": "Which data type is used to store a sequence of characters?",
            "options": ["int", "float", "str", "bool"],
            "answer": "str"
        },

        {
            "question": "Which function is used to display output in Python?",
            "options": ["display()", "show()", "print()", "output()"],
            "answer": "print()"
        },

        {
            "question": "Which of the following is a Python list?",
            "options": [
                "(1, 2, 3)",
                "[1, 2, 3]",
                "{1, 2, 3}",
                "<1, 2, 3>"
            ],
            "answer": "[1, 2, 3]"
        },

        {
            "question": "Which keyword is used to create a class in Python?",
            "options": ["class", "object", "define", "struct"],
            "answer": "class"
        },

        {
            "question": "Which operator is used for exponentiation in Python?",
            "options": ["^", "**", "//", "%%"],
            "answer": "**"
        }

    ],


    "Machine Learning": [

        {
            "question": "What is Machine Learning?",
            "options": [
                "A database",
                "A type of computer hardware",
                "A method where computers learn from data",
                "A programming language"
            ],
            "answer": "A method where computers learn from data"
        },

        {
            "question": "Which of these is a supervised learning algorithm?",
            "options": [
                "Decision Tree",
                "K-Means",
                "PCA",
                "Apriori"
            ],
            "answer": "Decision Tree"
        },

        {
            "question": "What is used to train a Machine Learning model?",
            "options": [
                "Data",
                "Keyboard",
                "Monitor",
                "Printer"
            ],
            "answer": "Data"
        },

        {
            "question": "Which algorithm is commonly used for classification?",
            "options": [
                "Decision Tree",
                "K-Means",
                "PCA",
                "Apriori"
            ],
            "answer": "Decision Tree"
        },

        {
            "question": "What does ML stand for?",
            "options": [
                "Machine Learning",
                "Machine Language",
                "Model Logic",
                "Modern Learning"
            ],
            "answer": "Machine Learning"
        },

        {
            "question": "Which learning uses labelled data?",
            "options": [
                "Supervised Learning",
                "Unsupervised Learning",
                "Reinforcement Learning",
                "Deep Search"
            ],
            "answer": "Supervised Learning"
        },

        {
            "question": "Which algorithm is used for clustering?",
            "options": [
                "Decision Tree",
                "K-Means",
                "Linear Regression",
                "Logistic Regression"
            ],
            "answer": "K-Means"
        }

    ],


    "SQL": [

        {
            "question": "What does SQL stand for?",
            "options": [
                "Structured Query Language",
                "Simple Query Language",
                "System Query Language",
                "Sequential Query Language"
            ],
            "answer": "Structured Query Language"
        },

        {
            "question": "Which command is used to retrieve data from a database?",
            "options": [
                "GET",
                "SELECT",
                "FETCH",
                "READ"
            ],
            "answer": "SELECT"
        },

        {
            "question": "Which command is used to add new data?",
            "options": [
                "ADD",
                "INSERT",
                "CREATE",
                "PUT"
            ],
            "answer": "INSERT"
        },

        {
            "question": "Which command is used to remove data?",
            "options": [
                "DELETE",
                "REMOVE",
                "DROP",
                "CLEAR"
            ],
            "answer": "DELETE"
        },

        {
            "question": "Which command is used to modify existing data?",
            "options": [
                "CHANGE",
                "UPDATE",
                "MODIFY",
                "EDIT"
            ],
            "answer": "UPDATE"
        },

        {
            "question": "Which clause is used to filter records?",
            "options": [
                "WHERE",
                "FILTER",
                "HAVING",
                "SEARCH"
            ],
            "answer": "WHERE"
        },

        {
            "question": "Which SQL command creates a table?",
            "options": [
                "MAKE TABLE",
                "CREATE TABLE",
                "NEW TABLE",
                "ADD TABLE"
            ],
            "answer": "CREATE TABLE"
        }

    ],


    "HTML": [

        {
            "question": "What does HTML stand for?",
            "options": [
                "HyperText Markup Language",
                "HighText Machine Language",
                "HyperText Machine Language",
                "Hyperlink Text Markup Language"
            ],
            "answer": "HyperText Markup Language"
        },

        {
            "question": "Which tag is used for the largest heading?",
            "options": [
                "<h1>",
                "<h6>",
                "<head>",
                "<heading>"
            ],
            "answer": "<h1>"
        },

        {
            "question": "Which tag is used to create a paragraph?",
            "options": [
                "<paragraph>",
                "<p>",
                "<para>",
                "<text>"
            ],
            "answer": "<p>"
        },

        {
            "question": "Which tag is used to create a link?",
            "options": [
                "<link>",
                "<a>",
                "<href>",
                "<url>"
            ],
            "answer": "<a>"
        },

        {
            "question": "Which tag is used to display an image?",
            "options": [
                "<image>",
                "<img>",
                "<pic>",
                "<src>"
            ],
            "answer": "<img>"
        }

    ]

}

# ----------------------------------------------------------------------
# Additional topics. "explanation" is shown in the answer review after a quiz.
# ----------------------------------------------------------------------

QUIZZES.update({

    "JavaScript": [
        {"question": "Which keyword declares a block-scoped variable that can be reassigned?",
         "options": ["var", "let", "const", "static"], "answer": "let",
         "explanation": "let is block-scoped and reassignable; const cannot be reassigned."},
        {"question": "Which method adds an element to the end of an array?",
         "options": ["push()", "pop()", "shift()", "unshift()"], "answer": "push()",
         "explanation": "push() appends; pop() removes the last element."},
        {"question": "What does === check in JavaScript?",
         "options": ["Value only", "Type only", "Value and type", "Reference only"],
         "answer": "Value and type",
         "explanation": "=== is strict equality: no type conversion happens."},
        {"question": "Which function converts a JSON string into an object?",
         "options": ["JSON.stringify()", "JSON.parse()", "JSON.object()", "JSON.decode()"],
         "answer": "JSON.parse()",
         "explanation": "JSON.parse() reads text; JSON.stringify() does the reverse."},
        {"question": "What does DOM stand for?",
         "options": ["Data Object Model", "Document Object Model", "Display Output Method", "Digital Order Mapping"],
         "answer": "Document Object Model",
         "explanation": "The DOM is the tree of elements JavaScript uses to read and change a page."},
        {"question": "Which keyword pauses an async function until a Promise resolves?",
         "options": ["wait", "pause", "await", "yield"], "answer": "await",
         "explanation": "await can only be used inside an async function (or a module)."},
    ],

    "CSS": [
        {"question": "Which property changes the text colour?",
         "options": ["font-color", "text-color", "color", "foreground"], "answer": "color",
         "explanation": "color sets the foreground (text) colour."},
        {"question": "Which CSS selector targets an element with id='menu'?",
         "options": [".menu", "#menu", "menu", "*menu"], "answer": "#menu",
         "explanation": "# selects by id, . selects by class."},
        {"question": "In the box model, which layer is closest to the content?",
         "options": ["Margin", "Border", "Padding", "Outline"], "answer": "Padding",
         "explanation": "From the inside out: content, padding, border, margin."},
        {"question": "Which declaration turns an element into a flex container?",
         "options": ["display: flex", "flex: container", "position: flex", "layout: flex"],
         "answer": "display: flex",
         "explanation": "display: flex enables flexbox layout for the children."},
        {"question": "Which unit is relative to the root element's font size?",
         "options": ["px", "em", "rem", "pt"], "answer": "rem",
         "explanation": "rem = root em; em is relative to the parent element's font size."},
        {"question": "Which property controls the stacking order of positioned elements?",
         "options": ["order", "z-index", "stack", "layer"], "answer": "z-index",
         "explanation": "Higher z-index values appear in front."},
    ],

    "Data Structures": [
        {"question": "Which data structure follows Last-In-First-Out (LIFO)?",
         "options": ["Queue", "Stack", "Array", "Graph"], "answer": "Stack",
         "explanation": "Like a pile of plates, the last item placed is the first removed."},
        {"question": "Which data structure follows First-In-First-Out (FIFO)?",
         "options": ["Stack", "Tree", "Queue", "Heap"], "answer": "Queue",
         "explanation": "Like a ticket line, the first person in is the first served."},
        {"question": "What is the time complexity of binary search on a sorted array?",
         "options": ["O(n)", "O(log n)", "O(n log n)", "O(1)"], "answer": "O(log n)",
         "explanation": "Each step halves the remaining search range."},
        {"question": "Which structure gives O(1) average lookup by key?",
         "options": ["Linked list", "Hash table", "Stack", "Binary tree"], "answer": "Hash table",
         "explanation": "A hash function maps the key straight to a storage slot."},
        {"question": "In a binary tree, each node has at most how many children?",
         "options": ["1", "2", "3", "Unlimited"], "answer": "2",
         "explanation": "Left child and right child."},
        {"question": "Which is a disadvantage of a linked list compared with an array?",
         "options": ["Slow insertion at the head", "No random access by index", "Fixed size", "Uses no memory"],
         "answer": "No random access by index",
         "explanation": "To reach the nth item you must walk the chain from the start."},
    ],

})
