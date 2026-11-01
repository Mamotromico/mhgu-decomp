struct Dst12 {
    unsigned long long v;
    unsigned int n;
};

extern "C" void func_6122fa28(struct Dst12 *dst, const unsigned long long *src)
{
    dst->v = *src;
    dst->n = 5;
}