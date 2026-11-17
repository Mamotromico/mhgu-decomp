extern "C" void func_600ee444(void *out, void *in)
{
    unsigned *o = (unsigned *)out;
    unsigned **p = (unsigned **)in;
    unsigned *obj = *p;
    unsigned (*fn)(void *) = (unsigned (*)(void *))*(void **)((char *)obj + 0xc);
    o[1] = fn(in);
}