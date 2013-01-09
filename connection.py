import Queue
import contextlib
import datetime
import threading


class ConnectionPool(object):
  """Simple connection pool."""
  def __init__(self, get_connection, size):
    """Constructor.

    Args:
      get_connection : () -> con - Generate a connection.  A connection can
        be anything, so long as whoever calls Get() is expecting it.
      size : int - Create this many connections.  They're created all at once.
    """
    # Lock protecting instance variables.  Held when Acquired and Released
    # are called.
    self.lock = threading.RLock()
    # {con: (checked_out_time, checked_out_by_user)}
    self.checked_out = {}
    # {con: time_since_last_checkout}
    self.checked_in = {}
    # LIFO queue ensures that the most recently used connection will be used
    # again.
    self.connections = Queue.LifoQueue(size)
    for i in range(size):
      con = get_connection()
      self.connections.put(con)
      self.checked_in[con] = datetime.datetime.utcnow()

  def Stats(self):
    """A snapshot of the current checked-in and checked-out connections.

    Of course since Get() is meant to be used from multiple threads, the
    snapshot may be out of date.
    Returns:
      checked_in : [(con, timedelta)] - Available connections, and their time
        since last check-out.
      checked_out : [(con, (timedelta, data))] - Checked out connections,
        how long they have been checked out, and some extra data given by Get().
    """
    now = datetime.datetime.utcnow()
    return (
        [(con, now - started) for (con, started) in self.checked_in.items()],
        [(con, (now - started, data)) for (con, (started, data))
            in self.checked_out.items()])

  def Acquired(self, con, data):
    """Called when the connection has been acquired, before it is given to
    the caller of Get().
    """
    del self.checked_in[con]
    self.checked_out[con] = (datetime.datetime.utcnow(), data)

  def Released(self, con, unused_data):
    """Called after a connection has been returned."""
    del self.checked_out[con]
    self.checked_in[con] = datetime.datetime.utcnow()
    self.connections.put(con)

  @contextlib.contextmanager
  def Get(self, timeout, data):
    """To be used with 'with' to get a connection.  Will yield None if there
      are no connections left.

    Args:
      timeout : double | None - Wait this many seconds for a new connection to
        become available before returning None.  If it's None, wait forever.
      data : anything - Store additional data about the checked-out connection,
        available via Stats().
    """
    try:
      con = self.connections.get(True, timeout)
    except Queue.Empty:
      con = None
    try:
      if con is not None:
        with self.lock:
          self.Acquired(con, data)
      yield con
    finally:
      if con is not None:
        with self.lock:
          self.Released(con, data)
