extern "C" void func_60117b4c(char *a, char *b)
{
    unsigned v = *(unsigned *)b;
    unsigned (*fn)(char *) = *(unsigned (**)(char *))(v + 0xc);
    unsigned r = fn(b);
    *(unsigned *)(a + 4) = r;
}