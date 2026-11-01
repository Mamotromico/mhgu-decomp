extern "C" unsigned long long func_6122fa74(const unsigned char *p)
{
    unsigned int tag = *(const unsigned int *)(p + 8);
    if (tag == 1) {
        return *(const unsigned long long *)p;
    }
    if (tag == 6) {
        return *(const unsigned long long *)p;
    }
    return 0;
}