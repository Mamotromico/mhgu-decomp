extern "C" int func_60120ecc(void *arg0, unsigned **arg1)
{
    int (*fn)(unsigned **) = (int (*)(unsigned **))(*arg1)[3];
    int result = fn(arg1);
    *(int *)((char *)arg0 + 4) = result;
    return result;
}