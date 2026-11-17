extern "C" char D_61788e54[];

extern "C" void func_60820f3c(void *);

extern "C" void func_60861cd4(void *p)
{
    *(void **)p = (void *)&D_61788e54[8];
    func_60820f3c(p);
}