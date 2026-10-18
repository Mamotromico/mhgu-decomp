typedef float func_v4f __attribute__((vector_size(16)));

extern "C" __attribute__((noinline)) func_v4f
func_60c4a194(func_v4f x)
{
    return __builtin_shufflevector(x, x, 0, 0, 0, 0);
}