# Implementing Persistent Storage for Call Data

## Current Implementation

The appointment bot currently uses in-memory storage for call data, which means all call transcripts and outcomes are lost when the server is restarted. Here's how the current system works:

1. **In-Memory Storage**: The `TwilioHandler` class maintains a dictionary called `calls` that stores call information:
   ```python
   self.calls[call_sid] = {
       'to': to_number,
       'status': call.status,
       'appointment_data': appointment_data,
       'transcript': [],
       'outcome': None
   }
   ```

2. **Data Flow**:
   - When a call is initiated, a new entry is created in the `calls` dictionary
   - During the call, the OpenAI handler captures the conversation transcript
   - At the end of the call, the transcript and outcome are updated in the `calls` dictionary
   - The data can be retrieved using the `get_call_transcript` and `get_call_outcome` methods

3. **Limitations**:
   - All data is lost when the server is restarted
   - Different instances of `TwilioHandler` don't share the same data
   - No historical record of calls is maintained

## Requirements for Persistent Storage

To implement persistent storage, we need to:

1. Save call data to a persistent medium (file or database)
2. Load existing data when the server starts
3. Update the persistent storage whenever call data changes
4. Ensure thread safety for concurrent access

## Implementation Options

### Option 1: JSON File Storage

**Approach**:
- Store call data in a JSON file
- Load the file when the `TwilioHandler` is initialized
- Save to the file whenever call data changes

**Implementation Steps**:
1. Add a file path configuration to the `.env` file
2. Add methods to load/save the `calls` dictionary from/to the JSON file
3. Call the save method whenever call data is updated
4. Add error handling for file operations

**Example Implementation**:
```python
def __init__(self):
    """Initialize the Twilio client and load existing call data."""
    # ... existing initialization code ...
    
    self.calls_file = os.getenv('CALLS_DATA_FILE', 'call_data.json')
    self.calls = self._load_calls_data()

def _load_calls_data(self):
    """Load call data from the JSON file."""
    if os.path.exists(self.calls_file):
        try:
            with open(self.calls_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading calls data: {e}")
    return {}

def _save_calls_data(self):
    """Save call data to the JSON file."""
    try:
        with open(self.calls_file, 'w') as f:
            json.dump(self.calls, f, indent=2)
    except Exception as e:
        print(f"Error saving calls data: {e}")

def update_call_transcript(self, call_sid: str, transcript: List[Dict[str, str]]) -> None:
    """Update the transcript for a call."""
    if call_sid in self.calls:
        self.calls[call_sid]['transcript'] = transcript
        self._save_calls_data()  # Save after updating
```

**Pros**:
- Simple implementation
- Human-readable storage format
- Easy to debug

**Cons**:
- Not suitable for high-volume applications
- Limited query capabilities
- Potential concurrency issues

### Option 2: SQLite Database

**Approach**:
- Use SQLite for persistent storage
- Create tables for calls, transcripts, and outcomes
- Query the database when retrieving call information

**Implementation Steps**:
1. Add SQLite dependency to `requirements.txt`
2. Create a database schema with tables for calls and related data
3. Modify `TwilioHandler` to use the database instead of the in-memory dictionary
4. Add methods for database operations (insert, update, select)

**Example Implementation**:
```python
def __init__(self):
    """Initialize the Twilio client and database connection."""
    # ... existing initialization code ...
    
    self.db_file = os.getenv('DB_FILE', 'appointment_bot.db')
    self._init_database()

def _init_database(self):
    """Initialize the database and create tables if they don't exist."""
    self.conn = sqlite3.connect(self.db_file)
    self.cursor = self.conn.cursor()
    
    # Create calls table
    self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS calls (
        sid TEXT PRIMARY KEY,
        to_number TEXT,
        status TEXT,
        appointment_data TEXT,
        outcome TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create transcript table
    self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcript_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_sid TEXT,
        role TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (call_sid) REFERENCES calls (sid)
    )
    ''')
    
    self.conn.commit()

def update_call_transcript(self, call_sid: str, transcript: List[Dict[str, str]]) -> None:
    """Update the transcript for a call."""
    # First, delete existing transcript items for this call
    self.cursor.execute("DELETE FROM transcript_items WHERE call_sid = ?", (call_sid,))
    
    # Insert new transcript items
    for item in transcript:
        self.cursor.execute(
            "INSERT INTO transcript_items (call_sid, role, content) VALUES (?, ?, ?)",
            (call_sid, item.get('role', 'unknown'), item.get('content', ''))
        )
    
    self.conn.commit()
```

**Pros**:
- More robust than file storage
- Better query capabilities
- Built-in concurrency handling

**Cons**:
- More complex implementation
- Requires additional dependency
- Slightly more overhead

### Option 3: Redis or Other In-Memory Store with Persistence

**Approach**:
- Use Redis for in-memory storage with persistence options
- Store call data as Redis hashes or JSON strings
- Configure Redis for periodic snapshots or append-only file persistence

**Implementation Steps**:
1. Add Redis dependency to `requirements.txt`
2. Set up Redis connection in `TwilioHandler`
3. Implement methods to save/retrieve data from Redis
4. Configure Redis persistence options

**Pros**:
- High performance
- Built for concurrent access
- Flexible persistence options

**Cons**:
- Additional infrastructure requirement
- More complex setup
- Overkill for simple applications

## Recommended Approach

For the appointment bot, the **JSON File Storage** option is recommended as the initial implementation due to:

1. Simplicity of implementation
2. No additional dependencies required
3. Sufficient for the current scale of the application

If the application grows or requires more complex querying capabilities, migrating to SQLite would be a logical next step.

## Implementation Plan

1. Add configuration for the data file path
2. Implement load/save methods in `TwilioHandler`
3. Update all methods that modify call data to save changes
4. Add error handling and logging
5. Add a maintenance method to clean up old call data

## Testing

To verify the implementation:
1. Start the server and make a test call
2. Restart the server
3. Verify that call data can still be retrieved
4. Check that the data file is being updated correctly

This approach will ensure that call transcripts and outcomes are preserved across server restarts, providing a more robust solution for the appointment bot.
