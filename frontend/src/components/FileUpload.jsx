import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Upload,
  File,
  FileText,
  Video,
  X,
  CheckCircle,
  AlertCircle,
  Download,
  Eye,
} from 'lucide-react';

const FileUpload = ({ 
  onFileUpload, 
  existingFile = null, 
  maxSize = 100 * 1024 * 1024, // 100MB default
  acceptedTypes = ['.pdf', '.ppt', '.pptx', '.mp4', '.mov'],
  disabled = false 
}) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadedFile, setUploadedFile] = useState(existingFile);

  const getFileIcon = (filename) => {
    const ext = filename.toLowerCase().split('.').pop();
    switch (ext) {
      case 'pdf':
        return <FileText className="h-8 w-8 text-red-500" />;
      case 'ppt':
      case 'pptx':
        return <File className="h-8 w-8 text-orange-500" />;
      case 'mp4':
      case 'mov':
        return <Video className="h-8 w-8 text-blue-500" />;
      default:
        return <File className="h-8 w-8 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    // Check file size
    if (file.size > maxSize) {
      return `File size must be less than ${formatFileSize(maxSize)}`;
    }

    // Check file type
    const fileExtension = '.' + file.name.toLowerCase().split('.').pop();
    if (!acceptedTypes.includes(fileExtension)) {
      return `File type not supported. Accepted types: ${acceptedTypes.join(', ')}`;
    }

    return null;
  };

  const simulateUpload = async (file) => {
    return new Promise((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          resolve();
        }
        setUploadProgress(Math.min(progress, 100));
      }, 200);
    });
  };

  const handleFileUpload = async (file) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate file upload progress
      await simulateUpload(file);

      // Create file object
      const fileData = {
        id: Date.now(), // In real app, this would come from server
        original_filename: file.name,
        file_size: file.size,
        file_type: file.type,
        upload_date: new Date().toISOString(),
        file_hash: 'sha256_' + Math.random().toString(36).substring(7), // Mock hash
        version: 1,
      };

      setUploadedFile(fileData);
      
      // Call parent callback
      if (onFileUpload) {
        onFileUpload(fileData);
      }

    } catch (error) {
      setError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      handleFileUpload(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'video/mp4': ['.mp4'],
      'video/quicktime': ['.mov'],
    },
    maxFiles: 1,
    disabled: disabled || uploading,
  });

  const removeFile = () => {
    setUploadedFile(null);
    setError('');
    if (onFileUpload) {
      onFileUpload(null);
    }
  };

  const downloadFile = () => {
    // In a real app, this would download from the server
    alert('Download functionality would be implemented here');
  };

  const viewFile = () => {
    // In a real app, this would open the file viewer
    alert('File viewer would be implemented here');
  };

  if (uploadedFile) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {getFileIcon(uploadedFile.original_filename)}
              <div>
                <h4 className="font-medium">{uploadedFile.original_filename}</h4>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(uploadedFile.file_size)} • Uploaded {new Date(uploadedFile.upload_date).toLocaleDateString()}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="secondary" className="text-xs">
                    Version {uploadedFile.version}
                  </Badge>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-xs text-green-600">Upload complete</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={viewFile}
              >
                <Eye className="mr-1 h-3 w-3" />
                View
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadFile}
              >
                <Download className="mr-1 h-3 w-3" />
                Download
              </Button>
              {!disabled && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={removeFile}
                >
                  <X className="mr-1 h-3 w-3" />
                  Remove
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-gray-400'}
              ${disabled || uploading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input {...getInputProps()} />
            
            {uploading ? (
              <div className="space-y-4">
                <Upload className="mx-auto h-12 w-12 text-primary animate-pulse" />
                <div>
                  <p className="text-lg font-medium">Uploading...</p>
                  <p className="text-sm text-muted-foreground">Please wait while your file is being uploaded</p>
                </div>
                <div className="max-w-xs mx-auto">
                  <Progress value={uploadProgress} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-1">{Math.round(uploadProgress)}% complete</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div>
                  <p className="text-lg font-medium">
                    {isDragActive ? 'Drop your file here' : 'Upload your presentation'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Drag and drop your file here, or click to browse
                  </p>
                </div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Supported formats: {acceptedTypes.join(', ')}</p>
                  <p>Maximum file size: {formatFileSize(maxSize)}</p>
                </div>
                <Button variant="outline" disabled={disabled}>
                  <Upload className="mr-2 h-4 w-4" />
                  Choose File
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FileUpload;

