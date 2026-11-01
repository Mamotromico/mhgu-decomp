extern "C" int func_607bda00(const unsigned short *p)
{
    int count = -1;
    unsigned short v;

    do {
        v = *p++;
        ++count;
    } while (v != 0);

    return count;
}