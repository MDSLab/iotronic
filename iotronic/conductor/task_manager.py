# coding=utf-8

# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
A context manager to perform a series of tasks on a set of resources.

:class:`TaskManager` is a context manager, created on-demand to allow
synchronized access to a node and its resources.

The :class:`TaskManager` will, by default, acquire an exclusive lock on
a node for the duration that the TaskManager instance exists. You may
create a TaskManager instance without locking by passing "shared=True"
when creating it, but certain operations on the resources held by such
an instance of TaskManager will not be possible. Requiring this exclusive
lock guards against parallel operations interfering with each other.

A shared lock is useful when performing non-interfering operations,
such as validating the driver interfaces.

An exclusive lock is stored in the database to coordinate between
:class:`iotronic.iotconductor.manager` instances,
that are typically deployed on different hosts.

:class:`TaskManager` methods, as well as driver methods, may be decorated to
determine whether their invocation requires an exclusive lock.

The TaskManager instance exposes certain node resources and properties as
attributes that you may access:

    task.context
        The context passed to TaskManager()
    task.shared
        False if Node is locked, True if it is not locked. (The
        'shared' kwarg arg of TaskManager())
    task.node
        The Node object
    task.ports
        Ports belonging to the Node
    task.driver
        The Driver for the Node, or the Driver based on the
        'driver_name' kwarg of TaskManager().

Example usage:

::

    with task_manager.acquire(context, node_id) as task:
        task.driver.power.power_on(task.node)

If you need to execute task-requiring code in a background thread, the
TaskManager instance provides an interface to handle this for you, making
sure to release resources when the thread finishes (successfully or if
an exception occurs). Common use of this is within the Manager like so:

::

    with task_manager.acquire(context, node_id) as task:
        <do some work>
        task.spawn_after(self._spawn_worker,
                         utils.node_power_action, task, new_state)

All exceptions that occur in the current GreenThread as part of the
spawn handling are re-raised. You can specify a hook to execute custom
code when such exceptions occur. For example, the hook is a more elegant
solution than wrapping the "with task_manager.acquire()" with a
try..exception block. (Note that this hook does not handle exceptions
raised in the background thread.):

::

    def on_error(e):
        if isinstance(e, Exception):
            ...

    with task_manager.acquire(context, node_id) as task:
        <do some work>
        task.set_spawn_error_hook(on_error)
        task.spawn_after(self._spawn_worker,
                         utils.node_power_action, task, new_state)

"""

import functools

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
import retrying

from iotronic.common import exception
from iotronic.common.i18n import _LW
from iotronic.common import states
from iotronic import objects

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


def require_exclusive_lock(f):
    """Decorator to require an exclusive lock.

    Decorated functions must take a :class:`TaskManager` as the first
    parameter. Decorated class methods should take a :class:`TaskManager`
    as the first parameter after "self".

    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        task = args[0] if isinstance(args[0], TaskManager) else args[1]
        if task.shared:
            raise exception.ExclusiveLockRequired()
        return f(*args, **kwargs)
    return wrapper


def acquire(context, node_id, shared=False, driver_name=None):
    """Shortcut for acquiring a lock on a Node.

    :param context: Request context.
    :param node_id: ID or UUID of node to lock.
    :param shared: Boolean indicating whether to take a shared or exclusive
                   lock. Default: False.
    :param driver_name: Name of Driver. Default: None.
    :returns: An instance of :class:`TaskManager`.

    """
    return TaskManager(context, node_id, shared=shared,
                       driver_name=driver_name)


class TaskManager(object):
    """Context manager for tasks.

    This class wraps the locking, driver loading, and acquisition
    of related resources (eg, Node and Ports) when beginning a unit of work.

    """

    def __init__(self, context, node_id, shared=False, driver_name=None):
        """Create a new TaskManager.

        Acquire a lock on a node. The lock can be either shared or
        exclusive. Shared locks may be used for read-only or
        non-disruptive actions only, and must be considerate to what
        other threads may be doing on the same node at the same time.

        :param context: request context
        :param node_id: ID or UUID of node to lock.
        :param shared: Boolean indicating whether to take a shared or exclusive
                       lock. Default: False.
        :param driver_name: The name of the driver to load, if different
                            from the Node's current driver.
        :raises: DriverNotFound
        :raises: NodeNotFound
        :raises: NodeLocked

        """

        self._spawn_method = None
        self._on_error_method = None

        self.context = context
        # self.node = None
        self.node = None
        self.shared = shared

        self.fsm = states.machine.copy()

        # NodeLocked exceptions can be annoying. Let's try to alleviate
        # some of that pain by retrying our lock attempts. The retrying
        # module expects a wait_fixed value in milliseconds.
        @retrying.retry(
            retry_on_exception=lambda e: isinstance(e, exception.NodeLocked),
            stop_max_attempt_number=CONF.conductor.node_locked_retry_attempts,
            wait_fixed=CONF.conductor.node_locked_retry_interval * 1000)
        def reserve_node():
            LOG.debug("Attempting to reserve node %(node)s",
                      {'node': node_id})
            self.node = objects.Node.reserve(context, CONF.host, node_id)

        try:
            """
            if not self.shared:
                reserve_node()
            else:
            """
            self.node = objects.Node.get(context, node_id)
            # self.ports = objects.Port.list_by_node_id(context, self.node.id)
            # self.driver = driver_factory.get_driver(driver_name or
            #                                       self.node.driver)

            # NOTE(deva): this handles the Juno-era NOSTATE state
            #             and should be deleted after Kilo is released
            '''
            if self.node.provision_state is states.NOSTATE:
                self.node.provision_state = states.AVAILABLE
                self.node.save()

            self.fsm.initialize(self.node.provision_state)
            '''
        except Exception:
            with excutils.save_and_reraise_exception():
                self.release_resources()

    def spawn_after(self, _spawn_method, *args, **kwargs):
        """Call this to spawn a thread to complete the task.

        The specified method will be called when the TaskManager instance
        exits.

        :param _spawn_method: a method that returns a GreenThread object
        :param args: args passed to the method.
        :param kwargs: additional kwargs passed to the method.

        """
        self._spawn_method = _spawn_method
        self._spawn_args = args
        self._spawn_kwargs = kwargs

    def set_spawn_error_hook(self, _on_error_method, *args, **kwargs):
        """Create a hook to handle exceptions when spawning a task.

        Create a hook that gets called upon an exception being raised
        from spawning a background thread to do a task.

        :param _on_error_method: a callable object, it's first parameter
            should accept the Exception object that was raised.
        :param args: additional args passed to the callable object.
        :param kwargs: additional kwargs passed to the callable object.

        """
        self._on_error_method = _on_error_method
        self._on_error_args = args
        self._on_error_kwargs = kwargs

    def release_resources(self):
        """Unlock a node and release resources.

        If an exclusive lock is held, unlock the node. Reset attributes
        to make it clear that this instance of TaskManager should no
        longer be accessed.
        """
        pass  # don't need it at the moment
        """
        if not self.shared:
            try:
                if self.node:
                    objects.Node.release(self.context, CONF.host, self.node.id)
            except exception.NodeNotFound:
                # squelch the exception if the node was deleted
                # within the task's context.
                pass
        self.node = None
        self.driver = None
        self.ports = None
        self.fsm = None
        """

    def _thread_release_resources(self, t):
        """Thread.link() callback to release resources."""
        self.release_resources()

    def process_event(self, event, callback=None, call_args=None,
                      call_kwargs=None, err_handler=None):
        """Process the given event for the task's current state.

        :param event: the name of the event to process
        :param callback: optional callback to invoke upon event transition
        :param call_args: optional \*args to pass to the callback method
        :param call_kwargs: optional \**kwargs to pass to the callback method
        :param err_handler: optional error handler to invoke if the
                callback fails, eg. because there are no workers available
                (err_handler should accept arguments node, prev_prov_state, and
                prev_target_state)
        :raises: InvalidState if the event is not allowed by the associated
                 state machine
        """
        # Advance the state model for the given event. Note that this doesn't
        # alter the node in any way. This may raise InvalidState, if this event
        # is not allowed in the current state.
        self.fsm.process_event(event)

        # stash current states in the error handler if callback is set,
        # in case we fail to get a worker from the pool
        if err_handler and callback:
            self.set_spawn_error_hook(err_handler, self.node,
                                      self.node.provision_state,
                                      self.node.target_provision_state)

        self.node.provision_state = self.fsm.current_state
        self.node.target_provision_state = self.fsm.target_state

        # set up the async worker
        if callback:
            # clear the error if we're going to start work in a callback
            self.node.last_error = None
            if call_args is None:
                call_args = ()
            if call_kwargs is None:
                call_kwargs = {}
            self.spawn_after(callback, *call_args, **call_kwargs)

        # publish the state transition by saving the Node
        self.node.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self._spawn_method is not None:
            # Spawn a worker to complete the task
            # The linked callback below will be called whenever:
            #   - background task finished with no errors.
            #   - background task has crashed with exception.
            #   - callback was added after the background task has
            #     finished or crashed. While eventlet currently doesn't
            #     schedule the new thread until the current thread blocks
            #     for some reason, this is true.
            # All of the above are asserted in tests such that we'll
            # catch if eventlet ever changes this behavior.
            thread = None
            try:
                thread = self._spawn_method(*self._spawn_args,
                                            **self._spawn_kwargs)

                # NOTE(comstud): Trying to use a lambda here causes
                # the callback to not occur for some reason. This
                # also makes it easier to test.
                thread.link(self._thread_release_resources)
                # Don't unlock! The unlock will occur when the
                # thread finshes.
                return
            except Exception as e:
                with excutils.save_and_reraise_exception():
                    try:
                        # Execute the on_error hook if set
                        if self._on_error_method:
                            self._on_error_method(e, *self._on_error_args,
                                                  **self._on_error_kwargs)
                    except Exception:
                        LOG.warning(_LW("Task's on_error hook failed to "
                                        "call %(method)s on node %(node)s"),
                                    {'method': self._on_error_method.__name__,
                                     'node': self.node.uuid})

                    if thread is not None:
                        # This means the link() failed for some
                        # reason. Nuke the thread.
                        thread.cancel()
                    self.release_resources()
        self.release_resources()
