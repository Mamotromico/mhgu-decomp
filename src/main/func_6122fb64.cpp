struct S {
    long long value;
    int key;
};

extern "C" void func_6122fb64(S *dst, S *src)
{
    long long v = 0;
    if (src->key == 5)
        v = src->value;
    dst->value = v;
}