extern "C" int func_610b0960(char *base, int key)
{
    unsigned int count = *(unsigned int *)(base + 0xd4f8);
    if (count == 0)
        return 0;
    void **array = *(void ***)(base + 0xd504);
    for (unsigned int i = 0; i < count; i++) {
        void *p = array[i];
        if (*(int *)((char *)p + 0x8) == key)
            return (int)(long)p;
    }
    return 0;
}