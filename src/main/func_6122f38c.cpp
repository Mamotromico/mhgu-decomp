namespace nn { namespace os { void *GetCurrentThread(); } }

extern "C" void *func_6122f38c(void) asm("func_6122f38c");

extern "C" void *func_6122f38c(void)
{
    return nn::os::GetCurrentThread();
}