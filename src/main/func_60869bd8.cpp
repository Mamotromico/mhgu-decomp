namespace nn { namespace os { struct MutexType; void LockMutex(MutexType*); } }

extern "C" void func_60869bd8(char *p) {
    nn::os::LockMutex((nn::os::MutexType *)(p + 0x3008));
}