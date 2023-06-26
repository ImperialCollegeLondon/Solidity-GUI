"""Tests for the gmsh_process module."""

from sys import platform

import pytest

from solidity_gui.main.gmsh_process import GmshDaemon, GmshProcess, _FunctionCall


@pytest.mark.skipif(
    platform == "darwin", reason="Queue.qsize() is not implemented on macOS"
)
class TestGmshProcess:
    """Collection of tests for GmshProcess."""

    function_name = "function"
    kwargs = dict(a="b")

    def test_gmsh_process_init(self, subscribe_mock):
        """Test instance initialisation."""
        gmsh_process = GmshProcess("default")
        subscribe_mock.assert_called_once_with(gmsh_process.stop_thread, "window.close")

    def test_call_function(self):
        """Test call_function method of class."""
        gmsh_process = GmshProcess("default")
        expected_output = "output"

        # pre-load something into the output queue as there in no
        # other process to do this
        gmsh_process.daemon._sync_out_queue.put(expected_output)

        assert gmsh_process.daemon._in_queue.qsize() == 0
        out = gmsh_process.call_function(self.function_name, **self.kwargs)
        assert gmsh_process.daemon._in_queue.qsize() == 1

        assert gmsh_process.daemon._in_queue.get() == _FunctionCall(
            name=self.function_name, kwargs=self.kwargs, asynchronous=False
        )
        assert out == expected_output

    def test_call_function_async(self, send_message_mock):
        """Test call_function_async method of class."""
        gmsh_process = GmshProcess("default")

        assert gmsh_process.daemon._in_queue.qsize() == 0
        gmsh_process.call_function_async(self.function_name, **self.kwargs)
        assert gmsh_process.daemon._in_queue.qsize() == 1

        assert gmsh_process.daemon._in_queue.get() == _FunctionCall(
            name=self.function_name, kwargs=self.kwargs, asynchronous=True
        )
        send_message_mock.assert_called_once_with(f"{self.function_name}.start")

    @pytest.mark.parametrize("asynchronous", (True, False))
    def test_daemon_call_function(self, asynchronous):
        """Test _call_function method of class."""
        return_value = "return_value"
        daemon = GmshDaemon()

        class WrapperMock:
            def function(self, **kwargs):
                self.kwargs = kwargs
                return return_value

        wrapper_mock = WrapperMock()
        daemon.geometry_wrapper = wrapper_mock

        daemon._in_queue.put(
            _FunctionCall(
                name=self.function_name, kwargs=self.kwargs, asynchronous=asynchronous
            )
        )

        daemon._call_function()
        # check the function on the mock was called
        assert wrapper_mock.kwargs == self.kwargs

        # check the correct value ends up in the correct queue
        if asynchronous:
            assert daemon._async_out_queue.qsize() == 1
            assert daemon._async_out_queue.get() == (
                self.function_name,
                return_value,
            )
        else:
            assert daemon._sync_out_queue.qsize() == 1
            assert daemon._sync_out_queue.get() == return_value
