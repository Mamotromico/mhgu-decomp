extern "C" unsigned func_6122c180(void *a, void *b)
{
    unsigned v = *(unsigned *)a;
    unsigned int bit = v >> 31;
    unsigned char c = *(unsigned char *)b;
    unsigned expected = 1 ^ bit;
    return (expected == c) ? 1 : 0;
}