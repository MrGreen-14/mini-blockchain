#ifndef EXPORT_H
#define EXPORT_H

#if defined(_WIN32)
#if defined(BUILDING_SHARED_LIB)
#define BLOCKCHAIN_API extern "C" __declspec(dllexport)
#else
#define BLOCKCHAIN_API extern "C" __declspec(dllimport)
#endif
#else
#define BLOCKCHAIN_API extern "C"
#endif

#endif