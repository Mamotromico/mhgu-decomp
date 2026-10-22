extern "C" void func_601afd60(void *a, void *b)
{
    *(unsigned int *)((char *)a + 0xc) = (unsigned int)b;
    unsigned int v = *(unsigned int *)((char *)b + 0x24);
    v = *(unsigned int *)(v + 0x14c);
    *(unsigned int *)((char *)a + 0x8) = v;
}