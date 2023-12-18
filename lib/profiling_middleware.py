import cProfile
import pstats
from line_profiler import LineProfiler





# This uses CProfile for profiling. No additional setup needed for this.
# This does the profiling of the end to end code for an HTTP request
# and prints the output in profiler_output.txt
class CProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start the profiler
        profiler = cProfile.Profile()
        profiler.enable()

        # Process the request
        response = self.get_response(request)

        # Stop the profiler
        profiler.disable()

        # Write the profiler output to a text file
        with open('profiler_output.txt', 'w') as f:
            sortby = 'cumulative'
            ps = pstats.Stats(profiler, stream=f).sort_stats(sortby)
            ps.print_stats()

        return response



# To use this This does a line by line profiling. To use this add @do_line_profile() as the first function decorator
# For ex
# @do_line_profile()
# def exercise_view(request):
#    ...
def do_line_profile(follow=[]):
    def inner(func):
        def profiled_func(*args, **kwargs):
            try:
                profiler = LineProfiler()
                profiler.add_function(func)
                for f in follow:
                    profiler.add_function(f)
                profiler.enable_by_count()
                result = func(*args, **kwargs)
                profiler.disable_by_count()
                return result
            finally:
                profiler.print_stats()
        return profiled_func
    return inner

